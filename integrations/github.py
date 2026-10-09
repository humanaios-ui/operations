"""GitHub API integration for Account Hub."""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import requests

from integrations.base import BaseAPIClient
from integrations.schemas import Event, EventType


logger = logging.getLogger(__name__)


class GitHubClient(BaseAPIClient):
    """Query GitHub API for repository and activity data."""

    SERVICE = "GitHub"
    AUTH_TYPE = "pat"  # Personal Access Token
    API_BASE_URL = "https://api.github.com"
    RATE_LIMIT = "5000 requests/hour (authenticated)"
    RATE_LIMIT_RESET_SECONDS = 3600

    def __init__(self, account_id: str, registry: Dict[str, Any]):
        """Initialize GitHub client."""
        super().__init__(account_id, registry)
        self.org = "humanaios-ui"  # From ACCOUNT_REGISTRY

    def _get_resource_types(self) -> List[str]:
        """Resource types we query from GitHub."""
        return ["repos", "commits", "pulls", "issues", "workflows"]

    def get_headers(self) -> Dict[str, str]:
        """Get request headers with auth token."""
        token = self.get_credential()
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HumanAIOS-AccountHub/1.0",
        }
        if token:
            headers["Authorization"] = f"token {token}"
        return headers

    def query(self, resource_type: str, **kwargs) -> List[Event]:
        """Query GitHub API for resource type."""
        if resource_type == "repos":
            return self.query_repos(**kwargs)
        elif resource_type == "commits":
            return self.query_commits(**kwargs)
        elif resource_type == "pulls":
            return self.query_pull_requests(**kwargs)
        elif resource_type == "issues":
            return self.query_issues(**kwargs)
        elif resource_type == "workflows":
            return self.query_workflows(**kwargs)
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")

    def query_repos(self, limit: int = 50) -> List[Event]:
        """Query organization repositories."""
        events = []
        try:
            url = f"{self.API_BASE_URL}/orgs/{self.org}/repos"
            params = {"per_page": min(limit, 100), "sort": "updated", "direction": "desc"}

            response = requests.get(url, headers=self.get_headers(), params=params, timeout=10)
            response.raise_for_status()

            for repo in response.json():
                if repo.get("updated_at"):
                    event = Event(
                        timestamp=datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00")),
                        service=self.SERVICE,
                        event_type=EventType.COMMIT,  # Generic activity
                        resource_id=repo["id"],
                        title=f"Repository updated: {repo['name']}",
                        url=repo["html_url"],
                        data={"repo": repo["name"], "pushed_at": repo.get("pushed_at")},
                    )
                    events.append(event)

            self._log_query("repos", "success", len(events))
            return events

        except requests.RequestException as e:
            logger.error(f"[GitHub] Failed to query repos: {e}")
            self._log_query("repos", "failure", 0)
            raise

    def query_commits(self, limit: int = 20) -> List[Event]:
        """Query recent commits across org repositories."""
        events = []
        try:
            # Get repos first
            repos_url = f"{self.API_BASE_URL}/orgs/{self.org}/repos"
            repos_response = requests.get(
                repos_url,
                headers=self.get_headers(),
                params={"per_page": 20, "sort": "updated"},
                timeout=10,
            )
            repos_response.raise_for_status()

            for repo in repos_response.json()[:10]:  # Check 10 most recent repos
                repo_name = repo["name"]
                try:
                    commits_url = f"{self.API_BASE_URL}/repos/{self.org}/{repo_name}/commits"
                    commits_response = requests.get(
                        commits_url,
                        headers=self.get_headers(),
                        params={"per_page": limit},
                        timeout=10,
                    )
                    commits_response.raise_for_status()

                    for commit in commits_response.json()[:5]:  # Last 5 commits per repo
                        commit_data = commit.get("commit", {})
                        event = Event(
                            timestamp=datetime.fromisoformat(
                                commit_data.get("author", {})
                                .get("date", "")
                                .replace("Z", "+00:00")
                            ),
                            service=self.SERVICE,
                            event_type=EventType.COMMIT,
                            resource_id=commit.get("sha", ""),
                            title=f"{repo_name}: {commit_data.get('message', 'Commit').split(chr(10))[0]}",
                            url=commit.get("html_url"),
                            data={"repo": repo_name, "author": commit.get("author", {}).get("name")},
                        )
                        events.append(event)
                except requests.RequestException as e:
                    logger.debug(f"[GitHub] Could not fetch commits from {repo_name}: {e}")

            self._log_query("commits", "success", len(events))
            return events

        except requests.RequestException as e:
            logger.error(f"[GitHub] Failed to query commits: {e}")
            self._log_query("commits", "failure", 0)
            raise

    def query_pull_requests(self, limit: int = 20) -> List[Event]:
        """Query open/closed pull requests."""
        events = []
        try:
            # Simplified: query from a main repo
            url = f"{self.API_BASE_URL}/repos/{self.org}/operations/pulls"
            params = {"per_page": limit, "sort": "updated", "direction": "desc"}

            response = requests.get(url, headers=self.get_headers(), params=params, timeout=10)
            response.raise_for_status()

            for pr in response.json():
                event = Event(
                    timestamp=datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00")),
                    service=self.SERVICE,
                    event_type=EventType.PULL_REQUEST,
                    resource_id=pr["id"],
                    title=f"PR #{pr['number']}: {pr['title'][:50]}",
                    url=pr["html_url"],
                    data={"state": pr["state"], "author": pr["user"]["login"]},
                )
                events.append(event)

            self._log_query("pulls", "success", len(events))
            return events

        except requests.RequestException as e:
            logger.error(f"[GitHub] Failed to query PRs: {e}")
            self._log_query("pulls", "failure", 0)
            raise

    def query_issues(self, limit: int = 20) -> List[Event]:
        """Query open/closed issues."""
        events = []
        try:
            url = f"{self.API_BASE_URL}/repos/{self.org}/operations/issues"
            params = {"per_page": limit, "sort": "updated", "direction": "desc"}

            response = requests.get(url, headers=self.get_headers(), params=params, timeout=10)
            response.raise_for_status()

            for issue in response.json():
                event = Event(
                    timestamp=datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00")),
                    service=self.SERVICE,
                    event_type=EventType.ISSUE,
                    resource_id=issue["id"],
                    title=f"Issue #{issue['number']}: {issue['title'][:50]}",
                    url=issue["html_url"],
                    data={"state": issue["state"], "author": issue["user"]["login"]},
                )
                events.append(event)

            self._log_query("issues", "success", len(events))
            return events

        except requests.RequestException as e:
            logger.error(f"[GitHub] Failed to query issues: {e}")
            self._log_query("issues", "failure", 0)
            raise

    def query_workflows(self) -> List[Event]:
        """Query recent workflow runs."""
        events = []
        try:
            url = f"{self.API_BASE_URL}/repos/{self.org}/operations/actions/runs"
            params = {"per_page": 20}

            response = requests.get(url, headers=self.get_headers(), params=params, timeout=10)
            response.raise_for_status()

            for run in response.json().get("workflow_runs", [])[:10]:
                event = Event(
                    timestamp=datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00")),
                    service=self.SERVICE,
                    event_type=EventType.DEPLOYMENT,  # Treat workflow as deployment
                    resource_id=run["id"],
                    title=f"Workflow: {run['name']} ({run['conclusion']})",
                    url=run["html_url"],
                    data={"status": run["status"], "conclusion": run.get("conclusion")},
                )
                events.append(event)

            self._log_query("workflows", "success", len(events))
            return events

        except requests.RequestException as e:
            logger.error(f"[GitHub] Failed to query workflows: {e}")
            self._log_query("workflows", "failure", 0)
            raise

    def health_check(self) -> bool:
        """Verify GitHub API access."""
        try:
            url = f"{self.API_BASE_URL}/user"
            response = requests.get(url, headers=self.get_headers(), timeout=5)
            is_ok = response.status_code == 200
            self.health.is_healthy = is_ok
            return is_ok
        except Exception as e:
            logger.warning(f"[GitHub] Health check failed: {e}")
            self.health.is_healthy = False
            return False
