/* HumanAIOS Operations Observatory E0
 * Public GitHub GET observations only; no authority, persistence, or write calls.
 * A "last update" of an issue/PR is NOT a discrete activity event or verified completion.
 */
(function (root) {
  "use strict";

  const REPOS = Object.freeze([
    "humanaios-ui/humanaios",
    "humanaios-ui/operations",
    "humanaios-ui/lasting-light-ai"
  ]);
  const DAYS = 28;
  const DAY_MS = 86400000;
  const PAGE_SIZE = 100;
  const MAX_PAGES = 4;
  const ATTENTION_LABELS = /human|review|decision|blocked|hold|needs.changes|attention|admission|ci.failure/i;
  const LABELS = {
    "humanaios-ui/humanaios": "HumanAIOS",
    "humanaios-ui/operations": "Operations",
    "humanaios-ui/lasting-light-ai": "Lasting Light AI"
  };

  // Require an explicit timezone (Z or numeric offset) so a bare local-time string is not
  // read in the viewer's timezone, and reject dates the engine would roll over (Feb 31).
  const TIMESTAMP = /^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(?:\.\d+)?(Z|[+-]\d\d:\d\d)$/;
  function dateMs(s) {
    if (typeof s !== "string") return null;
    const m = TIMESTAMP.exec(s);
    if (!m) return null;
    const [year, month, day, hour, minute, second] = m.slice(1, 7).map(Number);
    if (month < 1 || month > 12 || hour > 23 || minute > 59 || second > 59) return null;
    if (day < 1 || day > new Date(Date.UTC(year, month, 0)).getUTCDate()) return null;
    const t = Date.parse(s);
    return Number.isFinite(t) ? t : null;
  }

  function safeRecord(raw, repo, nowMs) {
    if (!raw || typeof raw !== "object" || !Number.isInteger(raw.number) || raw.number < 1) return null;
    if (!["open", "closed"].includes(raw.state)) return null;
    if (!REPOS.includes(repo)) return null;
    const isPR = Boolean(raw.pull_request);
    const kind = isPR ? "pull" : "issues";
    const url = "https://github.com/" + repo + "/" + kind + "/" + raw.number;
    // Match exact canonical origin and repository path. Ignore untrusted API URL fields.
    if (raw.html_url !== url) return null;
    const updated = dateMs(raw.updated_at);
    if (updated === null || updated > nowMs + 300000) return null;
    const created = dateMs(raw.created_at);
    if (created === null || created > updated) return null;
    const closed = dateMs(raw.closed_at);
    const labels = Array.isArray(raw.labels) ? raw.labels
      .filter(x => x && typeof x.name === "string")
      .map(x => x.name.slice(0, 70)) : [];
    return {
      key: repo + "#" + raw.number,
      repository: repo,
      number: raw.number,
      kind: isPR ? "PR" : "ISSUE",
      title: String(raw.title || "Untitled").slice(0, 240),
      state: raw.state,
      url: url,
      updated_at: new Date(updated).toISOString(),
      updated_ms: updated,
      created_ms: created,
      closed_ms: closed,
      labels: labels
    };
  }

  function project(repo, rawItems, observedAt, coverage) {
    if (!REPOS.includes(repo)) throw Error("Repository not allowed");
    const nowMs = typeof observedAt === "number" ? observedAt : dateMs(observedAt);
    if (nowMs === null || !Number.isFinite(nowMs)) throw Error("Invalid observation time");
    const cutoff = nowMs - DAYS * DAY_MS;
    const seen = new Set();
    const records = [];
    let rejected = 0;
    let duplicates = 0;
    for (const raw of rawItems) {
      const item = safeRecord(raw, repo, nowMs);
      if (!item) { rejected++; continue; }
      if (item.updated_ms < cutoff || item.updated_ms > nowMs) continue;
      if (seen.has(item.key)) { duplicates++; continue; }
      seen.add(item.key);
      records.push(item);
    }
    records.sort((a, b) => b.updated_ms - a.updated_ms || a.number - b.number);
    const prs = records.filter(x => x.kind === "PR");
    const issues = records.filter(x => x.kind === "ISSUE");
    const buckets = Array(DAYS).fill(0);
    for (const x of records) {
      const index = Math.min(DAYS - 1, Math.floor((x.updated_ms - cutoff) / DAY_MS));
      if (index >= 0 && index < DAYS) buckets[index] += 1;
    }
    const week = records.filter(x => x.updated_ms >= nowMs - 7 * DAY_MS).length;
    const previousWeek = records.filter(x => x.updated_ms < nowMs - 7 * DAY_MS &&
      x.updated_ms >= nowMs - 14 * DAY_MS).length;
    const attention = records.filter(x => x.state === "open").map(x => {
      const flagged = x.labels.some(label => ATTENTION_LABELS.test(label));
      return Object.assign({}, x, {
        basis: flagged ? "SOURCE_LABEL_MATCH" : "OPEN_ITEM_CANDIDATE",
        note: flagged ? "Open item; source label suggests review/hold" : "Open item; attention unconfirmed",
        age_days: Math.floor((nowMs - x.updated_ms) / DAY_MS)
      });
    }).sort((a, b) => {
      const ax = a.basis === "SOURCE_LABEL_MATCH" ? 0 : 1;
      const bx = b.basis === "SOURCE_LABEL_MATCH" ? 0 : 1;
      return ax - bx || b.age_days - a.age_days || a.number - b.number;
    });
    return {
      repository: repo,
      display_name: LABELS[repo],
      observed_at: new Date(nowMs).toISOString(),
      window_start: new Date(cutoff).toISOString(),
      coverage: coverage,
      rejected: rejected,
      duplicates: duplicates,
      fetched_records: rawItems.length,
      touched_prs: prs.length,
      touched_issues: issues.length,
      newly_created_prs: prs.filter(x => x.created_ms !== null && x.created_ms >= cutoff).length,
      newly_created_issues: issues.filter(x => x.created_ms !== null && x.created_ms >= cutoff).length,
      currently_closed_prs: prs.filter(x => x.state === "closed").length,
      currently_closed_issues: issues.filter(x => x.state === "closed").length,
      open_touched_prs: prs.filter(x => x.state === "open").length,
      open_touched_issues: issues.filter(x => x.state === "open").length,
      last_touch_buckets: buckets,
      last_touch_last_7d: week,
      last_touch_prior_7d: previousWeek,
      records: records,
      attention: attention
    };
  }

  async function fetchRepository(repo, nowMs, fetchFn, options) {
    const timeoutMs = options && Number.isFinite(options.timeoutMs) ? options.timeoutMs : 12000;
    if (!REPOS.includes(repo)) throw Error("Repository not allowed");
    const cutoff = nowMs - DAYS * DAY_MS;
    const items = [];
    let coverage = "PARTIAL_PAGE_LIMIT";
    let reason = "Pagination capped at " + MAX_PAGES + " pages";
    let pages = 0;
    let oldestPreviousPage = Infinity;
    for (let p = 1; p <= MAX_PAGES; p++) {
      const url = "https://api.github.com/repos/" + repo +
        "/issues?state=all&sort=updated&direction=desc&per_page=" + PAGE_SIZE + "&page=" + p;
      const controller = typeof AbortController === "function" ? new AbortController() : null;
      const timeout = controller ? setTimeout(() => controller.abort(), timeoutMs) : null;
      // The timer stays active until the body is parsed, so a stalled body read is aborted too.
      let page;
      try {
        const response = await fetchFn(url, {
          method: "GET", cache: "no-store",
          headers: { "Accept": "application/vnd.github+json" },
          ...(controller ? {signal: controller.signal} : {})
        });
        if (!response || !response.ok) {
          const status = response && response.status ? response.status : "unknown";
          return {items, coverage: items.length ? "PARTIAL_HTTP_ERROR" : "UNAVAILABLE",
            reason: "GitHub HTTP " + status + " (rate limit or connectivity possible)", pages};
        }
        try { page = await response.json(); }
        catch (err) {
          const aborted = controller && controller.signal.aborted;
          return {items, coverage: items.length ? "PARTIAL_INVALID_JSON" : "UNAVAILABLE",
            reason: aborted ? "GitHub response body timed out" : "GitHub response is not valid JSON", pages};
        }
      } catch (err) {
        return {items, coverage: items.length ? "PARTIAL_FETCH_ERROR" : "UNAVAILABLE",
          reason: "GitHub request failed: " + String(err && err.name || "network"), pages};
      } finally {
        if (timeout) clearTimeout(timeout);
      }
      if (!Array.isArray(page) || page.length > PAGE_SIZE) {
        return {items, coverage: items.length ? "PARTIAL_INVALID_RESPONSE" : "UNAVAILABLE",
          reason: "Unexpected GitHub response shape", pages};
      }
      // GitHub promises newest-first records. Check the promise on every
      // page, including the final short page, before claiming completeness.
      const times = page.map(x => dateMs(x && x.updated_at));
      if (times.some(t => t === null) || times.some((t, i) => i > 0 && t > times[i-1]) ||
          (times.length && times[0] > oldestPreviousPage)) {
        coverage = "PARTIAL_UNSORTED";
        reason = "GitHub results have invalid or unsorted updated timestamps";
        break;
      }
      pages += 1;
      items.push(...page);
      if (times.length) oldestPreviousPage = times[times.length - 1];
      if (page.length < PAGE_SIZE) {
        coverage = "COMPLETE_WINDOW";
        reason = "End of paginated GitHub results";
        break;
      }
      if (times[times.length - 1] < cutoff) {
        coverage = "COMPLETE_WINDOW";
        reason = "Reached records older than the 28-day cutoff";
        break;
      }
    }
    return {items, coverage, reason, pages};
  }

  function text(el, value) { el.textContent = String(value); return el; }
  function element(tag, cls, content) {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (content !== undefined) text(el, content);
    return el;
  }
  function link(url, label) {
    const a = element("a", "", label);
    a.href = url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    return a;
  }
  function fmtTime(s) {
    const v = dateMs(s);
    return v === null ? "unknown" : new Date(v).toLocaleString();
  }
  function clear(el) { el.replaceChildren(); }
  function buildBars(data, box, label) {
    clear(box);
    box.setAttribute("aria-label", label);
    const max = Math.max(1, ...data);
    data.forEach((n, i) => {
      const bar = element("span", "bar");
      bar.style.height = Math.max(3, Math.round(n / max * 100)) + "%";
      bar.title = n + " items last updated in 24-hour bucket " + (i+1) + " of 28";
      box.appendChild(bar);
    });
  }
  function populateCard(node, projected) {
    clear(node);
    const head = element("div", "card-head");
    head.appendChild(element("h2", "", projected.display_name));
    head.appendChild(element("span", "coverage " + (projected.coverage === "COMPLETE_WINDOW" ? "good" : "warn"),
      projected.coverage.replaceAll("_", " ")));
    node.appendChild(head);
    node.appendChild(element("div", "repo-id", projected.repository));
    if (projected.coverage === "UNAVAILABLE") {
      node.appendChild(element("p", "warn-text", "No public GitHub data available. No counts shown."));
      return;
    }
    if (projected.coverage === "STALE_LAST_SUCCESS") {
      node.appendChild(element("p", "warn-text", "Cached data from the last successful read, not current. Observed " +
        fmtTime(projected.observed_at) + " for the window " + fmtTime(projected.window_start) + " to " +
        fmtTime(projected.observed_at) + ". Refresh failed: " + (projected.stale_reason || "unknown reason") + "."));
    }
    const metrics = element("div", "metrics");
    [["PRs last updated",projected.touched_prs],["Issues last updated",projected.touched_issues],
      ["PRs created",projected.newly_created_prs],["Issues created",projected.newly_created_issues],
      ["Open PRs in window",projected.open_touched_prs],["Open issues in window",projected.open_touched_issues]]
      .forEach(([label,n]) => {
        const metric = element("div", "metric");
        metric.appendChild(element("strong", "", (projected.coverage === "COMPLETE_WINDOW" && projected.rejected === 0 && !projected.duplicates ? "" : "≥") + n));
        metric.appendChild(element("span", "", label));
        metrics.appendChild(metric);
      });
    node.appendChild(metrics);
    const block = element("div", "kinetics");
    block.appendChild(element("strong", "", "Kinetics — last-update distribution"));
    const bars = element("div", "bars");
    buildBars(projected.last_touch_buckets, bars, "28 rolling 24-hour buckets of issue/PR last updates");
    block.appendChild(bars);
    block.appendChild(element("div", "hint", "Last 7d: " + projected.last_touch_last_7d +
      " · Prior 7d: " + projected.last_touch_prior_7d + " · One last update per item, not event volume."));
    node.appendChild(block);
    const recent = element("div", "recent");
    recent.appendChild(element("h3", "", "Recent source records"));
    projected.records.slice(0, 4).forEach(x => {
      const row = element("div", "source-row");
      row.appendChild(link(x.url, x.kind + " #" + x.number + " — " + x.title));
      row.appendChild(element("span", "hint", x.state.toUpperCase() + " · " + fmtTime(x.updated_at)));
      recent.appendChild(row);
    });
    if (!projected.records.length) recent.appendChild(element("p", "hint", "No records updated in window."));
    node.appendChild(recent);
    if (projected.rejected) node.appendChild(element("p", "warn-text", projected.rejected +
      " malformed/foreign records rejected; displayed sample is incomplete."));
    if (projected.duplicates) node.appendChild(element("p", "warn-text", projected.duplicates +
      " duplicate record(s) in the source pages; paging may have shifted, so counts are lower bounds."));
  }

  function renderAttention(snapshots, box) {
    clear(box);
    const items = snapshots.flatMap(s => s.attention.map(x => ({
      repository: s.repository, coverage: s.coverage, observed_at: s.observed_at, item: x
    }))).sort((a, b) => {
      const aRank = a.item.basis === "SOURCE_LABEL_MATCH" ? 0 : 1;
      const bRank = b.item.basis === "SOURCE_LABEL_MATCH" ? 0 : 1;
      return aRank-bRank || b.item.age_days-a.item.age_days || a.item.number-b.item.number;
    }).slice(0, 12);
    if (!items.length) {
      box.appendChild(element("p", "hint", "No open records observed in the 28-day source sample."));
      return;
    }
    items.forEach(entry => {
      const r = entry.item;
      const item = element("div", "attention-row");
      item.appendChild(link(r.url, r.kind + " #" + r.number + " · " + r.title));
      item.appendChild(element("p", "hint", r.repository + " · " + r.note +
        " · last touched " + r.age_days + "d before " + fmtTime(entry.observed_at) + " · " + entry.coverage));
      box.appendChild(item);
    });
  }

  function boot() {
    const refreshButton = document.getElementById("refresh");
    const status = document.getElementById("status");
    const attention = document.getElementById("attention");
    const cards = {};
    REPOS.forEach(r => { cards[r] = document.getElementById("repo-" + r.split("/")[1]); });
    let previous = new Map();
    let working = false;

    async function refresh() {
      if (working) return;
      working = true;
      refreshButton.disabled = true;
      text(status, "READING public GitHub API · no credentials or writes");
      const nowMs = Date.now();
      const result = await Promise.all(REPOS.map(async r => {
        const fetched = await fetchRepository(r, nowMs, fetch.bind(root));
        if (fetched.coverage === "UNAVAILABLE") {
          const old = previous.get(r);
          if (old) return Object.assign({}, old, {
            coverage: "STALE_LAST_SUCCESS", stale_reason: fetched.reason
          });
        }
        const projection = project(r, fetched.items, nowMs, fetched.coverage);
        projection.reason = fetched.reason;
        projection.pages = fetched.pages;
        if (fetched.coverage === "COMPLETE_WINDOW") previous.set(r, projection);
        return projection;
      }));
      result.forEach(x => populateCard(cards[x.repository], x));
      renderAttention(result.filter(x => x.coverage !== "UNAVAILABLE"), attention);
      const allComplete = result.every(x => x.coverage === "COMPLETE_WINDOW" && x.rejected === 0 && !x.duplicates);
      text(status, (allComplete ? "SOURCE WINDOW COMPLETE" : "PARTIAL / STALE / UNAVAILABLE — SEE REPOSITORIES") +
        " · checked " + new Date(nowMs).toLocaleString() +
        " · window since " + new Date(nowMs - DAYS*DAY_MS).toLocaleString() +
        " · GitHub issue/PR updates ≠ runtime health");
      document.getElementById("source-details").textContent =
        result.map(x => x.display_name + ": " + x.coverage +
        (x.reason ? " (" + x.reason + ")" : "")).join(" | ");
      refreshButton.disabled = false;
      working = false;
    }
    refreshButton.addEventListener("click", () => { refresh().catch(e => {
      text(status, "UNAVAILABLE: " + String(e && e.message || "unknown error") +
        " · no fresh or verified metrics");
      refreshButton.disabled = false;
      working = false;
    }); });
    refreshButton.click();
  }

  const API = { REPOS, DAYS, MAX_PAGES, dateMs, safeRecord, project, fetchRepository };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof document !== "undefined") boot();
})(typeof globalThis !== "undefined" ? globalThis : this);
