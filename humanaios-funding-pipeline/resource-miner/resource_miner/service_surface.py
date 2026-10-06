from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SERVICE_SURFACE_CLASSES = {
    "NETWORK_TRANSPORT",
    "WEB_APPLICATION",
    "API_SERVICE",
    "REALTIME_EVENT",
    "AUTH_IDENTITY",
    "DISCOVERY_METADATA",
    "CLIENT_BROWSER",
    "STORAGE_CLOUD",
    "ADMIN_OPS_MANAGEMENT",
    "THIRD_PARTY_EMBEDDED",
}

SERVICE_SURFACE_TAXONOMY: dict[str, dict[str, Any]] = {
    "NETWORK_TRANSPORT": {
        "description": "Network and transport-layer service exposure.",
        "examples": [
            "HTTP/HTTPS",
            "alternate HTTP ports such as 8080/8443/8000/3000",
            "WebSocket transport",
            "HTTP/2",
            "HTTP/3 / QUIC",
            "gRPC transport",
            "SSH",
            "FTP",
            "SMTP",
            "database listeners",
            "Docker/Kubernetes APIs",
        ],
    },
    "WEB_APPLICATION": {
        "description": "Browser-facing application routes and workflows.",
        "examples": [
            "static assets",
            "authentication flows",
            "search/filter/pagination",
            "forms",
            "file transfer workflows",
            "admin/dashboard/CMS interfaces",
            "health/status/metrics routes",
            "debug/configuration exposure routes",
        ],
    },
    "API_SERVICE": {
        "description": "Machine-facing application service interfaces.",
        "examples": [
            "REST",
            "GraphQL",
            "SOAP/WSDL",
            "JSON-RPC",
            "XML-RPC",
            "gRPC-Web",
            "webhook test surfaces",
            "OpenAPI/Swagger documentation",
            "Postman collections",
            "GraphiQL",
        ],
    },
    "REALTIME_EVENT": {
        "description": "Real-time, streaming, or event-oriented service interfaces.",
        "examples": [
            "WebSocket",
            "Server-Sent Events",
            "long polling",
            "Socket.IO",
            "SignalR",
            "MQTT over WebSocket",
        ],
    },
    "AUTH_IDENTITY": {
        "description": "Authentication, authorization, session, and federation services.",
        "examples": [
            "OAuth",
            "OpenID Connect",
            "OIDC discovery",
            "authorization/token/userinfo endpoints",
            "SAML metadata",
            "JWT/JWKS",
            "session cookies",
            "CSRF tokens",
            "MFA workflows",
        ],
    },
    "DISCOVERY_METADATA": {
        "description": "Public discovery, policy, metadata, and application-association surfaces.",
        "examples": [
            "robots.txt",
            "sitemap.xml",
            "security.txt",
            "humans.txt",
            "manifest.json",
            "service-worker.js",
            ".well-known resources",
            "favicon.ico",
            "crossdomain.xml",
            "clientaccesspolicy.xml",
            "ads.txt",
            "app-ads.txt",
        ],
    },
    "CLIENT_BROWSER": {
        "description": "Client-side and browser-exposed application capabilities.",
        "examples": [
            "JavaScript/source maps",
            "client-side endpoints/configuration",
            "HTML comments/hidden fields",
            "cookies",
            "localStorage/sessionStorage/IndexedDB",
            "Web Workers/Service Workers/WebAssembly",
            "iframes/postMessage",
            "permission-gated browser APIs",
        ],
    },
    "STORAGE_CLOUD": {
        "description": "Object storage, CDN, database, and cloud-hosted data surfaces.",
        "examples": [
            "S3-compatible object storage",
            "Azure Blob Storage",
            "Google Cloud Storage",
            "CDN endpoints",
            "database/object-store service endpoints",
        ],
    },
    "ADMIN_OPS_MANAGEMENT": {
        "description": "Administrative, CI/CD, orchestration, observability, and management surfaces.",
        "examples": [
            "Jenkins",
            "GitLab",
            "GitHub Actions runners",
            "Kubernetes API",
            "Docker API",
            "Prometheus",
            "Grafana",
            "Kibana",
            "database administration interfaces",
            "logs/metrics/tracing endpoints",
        ],
    },
    "THIRD_PARTY_EMBEDDED": {
        "description": "Third-party services embedded into or called by an application.",
        "examples": [
            "analytics",
            "advertising",
            "CDNs",
            "social widgets",
            "payment gateways",
            "chat/support widgets",
            "maps",
            "fonts",
            "embedded video",
        ],
    },
}


@dataclass(frozen=True)
class ServiceSurfaceBinding:
    requirement_id: str
    surface_classes: list[str]
    evidence: list[dict[str, Any]]
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "surface_classes": list(self.surface_classes),
            "evidence": list(self.evidence),
            "authority_effect": self.authority_effect,
        }


def normalize_surface_classes(values: list[str]) -> list[str]:
    normalized = sorted({str(value).strip().upper() for value in values if str(value).strip()})
    unknown = sorted(set(normalized) - SERVICE_SURFACE_CLASSES)
    if unknown:
        raise ValueError(f"unsupported service surface classes: {unknown}")
    return normalized


def taxonomy_snapshot() -> dict[str, Any]:
    return {
        key: {
            "description": value["description"],
            "examples": list(value["examples"]),
            "scope_effect": "NONE",
            "authorization_effect": "NONE",
        }
        for key, value in sorted(SERVICE_SURFACE_TAXONOMY.items())
    }
