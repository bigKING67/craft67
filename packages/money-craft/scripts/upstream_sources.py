"""Public upstream observations. Checks never advance review or adoption records."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

NORMALIZER = "article-text-structure.v1"
CAPTURE_SCHEMA = "money-craft.doc-capture.v1"
SNAPSHOT_SCHEMA = "money-craft.doc-snapshot.v1"
SHA = re.compile(r"[0-9a-f]{40}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
MAX_RESPONSE_BYTES = 16 * 1024 * 1024


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return result


def public_url(value: str) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment or parsed.port):
        raise ValueError("expected a public HTTPS URL without credentials, query, fragment or port")
    return urlunsplit(("https", parsed.netloc.lower(), parsed.path.rstrip("/") or "/", "", ""))


def in_docs(url: str, root: str) -> bool:
    return url == root or url.startswith(root.rstrip("/") + "/")


class ArticleParser(HTMLParser):
    """Extract the same article textContent used by browser captures, without page chrome."""

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.parts: list[str] = []
        self.structure: list[list[str]] = []
        self.articles = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "article" and "article" not in self.stack:
            self.articles += 1
        if tag not in self.VOID:
            self.stack.append(tag)
        if "article" in self.stack and tag in {"table", "tr", "td", "th", "pre"}:
            attributes = dict(attrs)
            self.structure.append(["open", tag, attributes.get("rowspan") or "", attributes.get("colspan") or ""])

    def handle_endtag(self, tag: str) -> None:
        if "article" in self.stack and tag in {"table", "tr", "td", "th", "pre"}:
            self.structure.append(["close", tag])
        if tag in self.stack:
            self.stack = self.stack[:len(self.stack) - 1 - self.stack[::-1].index(tag)]

    def handle_data(self, data: str) -> None:
        if "article" in self.stack and not {"script", "style"}.intersection(self.stack):
            self.parts.append(data)
            if {"table", "pre"}.intersection(self.stack):
                if self.structure and self.structure[-1][0] == "text":
                    self.structure[-1][1] += data
                else:
                    self.structure.append(["text", data])


def normalize_article(text: str) -> str:
    # Preserve internal whitespace: it may be meaningful in code, literals or tables.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"最后于\s*\d{4}年\d{1,2}月\d{1,2}日\s*更新\s*$", "", text)
    return text.strip()


def structure_digest(structure: list[list[str]]) -> str:
    return hashlib.sha256(json.dumps(structure, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def snapshot_revision(pages: list[dict[str, Any]]) -> str:
    identity = [{key: page[key] for key in ("url", "final_url", "title", "sha256")}
                for page in sorted(pages, key=lambda item: item["url"])]
    return hashlib.sha256(json.dumps(identity, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def make_snapshot(capture: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    if capture.get("schema") != CAPTURE_SCHEMA or capture.get("source_id") != source["id"]:
        raise ValueError("capture schema or source identity mismatch")
    timestamp(capture["captured_at"])
    if capture.get("catalog_complete") is not True:
        raise ValueError("a fully enumerated public catalog is required; partial captures cannot prove removals")
    root = public_url(source["url"])
    catalog = [public_url(url) for url in capture["catalog_urls"]]
    if not catalog or len(set(catalog)) != len(catalog) or root not in catalog:
        raise ValueError("catalog must contain the root and unique URLs")
    if any(not in_docs(url, root) for url in catalog):
        raise ValueError("catalog URL is outside this documentation source")
    pages = []
    for page in capture["pages"]:
        url = public_url(page["url"])
        final_url = public_url(page.get("final_url", url))
        if page.get("status") != 200 or not in_docs(final_url, root):
            raise ValueError("page failed or redirected outside this documentation source")
        if "html" in page:
            parser = ArticleParser()
            parser.feed(page["html"])
            if parser.articles != 1:
                raise ValueError("expected one documentation article; not an error or login page")
            text = "".join(parser.parts)
            structural_hash = structure_digest(parser.structure)
        else:
            text = page["text"]
            structural_hash = page.get("structure_sha256")
        if not isinstance(structural_hash, str) or not DIGEST.fullmatch(structural_hash):
            raise ValueError("text capture requires a browser-computed table/code structure_sha256")
        title = page["title"].strip()
        text = normalize_article(text)
        if not title or not text or re.search(
            r"access denied|just a moment|verify you are human|enable javascript and cookies|sign in to continue",
            title + "\n" + text[:500], re.I,
        ):
            raise ValueError("missing article or access challenge; no snapshot accepted")
        pages.append({"url": url, "final_url": final_url, "title": title,
                      "sha256": hashlib.sha256((text + "\n" + structural_hash).encode()).hexdigest()})
    if len(pages) != len(catalog) or {p["url"] for p in pages} != set(catalog):
        raise ValueError("page coverage must exactly match the complete catalog")
    return {"schema": SNAPSHOT_SCHEMA, "source_id": source["id"],
            "captured_at": capture["captured_at"], "normalizer": NORMALIZER,
            "catalog_complete": True, "revision": snapshot_revision(pages),
            "pages": sorted(pages, key=lambda item: item["url"])}


def document_delta(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, str]]:
    if before["normalizer"] != after["normalizer"]:
        raise ValueError("normalizer changed; explicitly review a new baseline")
    old = {item["url"]: item for item in before["pages"]}
    new = {item["url"]: item for item in after["pages"]}
    changes = []
    for url in sorted(old.keys() | new.keys()):
        if url not in old:
            kind = "added"
        elif url not in new:
            kind = "removed_from_catalog"
        elif old[url]["final_url"] != new[url]["final_url"]:
            kind = "redirected"
        elif any(old[url][key] != new[url][key] for key in ("sha256", "title")):
            kind = "modified"
        else:
            continue
        changes.append({"path": url, "change": kind})
    return changes


def fetch_json(url: str) -> Any:
    request = Request(url, headers={"User-Agent": "money-craft-upstream-status",
                                   "Accept": "application/vnd.github+json"})
    with urlopen(request, timeout=15) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("upstream response exceeds bounded read limit")
    return json.loads(raw)


def github_api(source: dict[str, Any]) -> str:
    url = public_url(source["url"])
    parsed = urlsplit(url)
    if parsed.hostname != "github.com" or len(parsed.path.strip("/").split("/")) != 2:
        raise ValueError("Git sources currently require a public GitHub repository")
    return "https://api.github.com/repos" + parsed.path


def tracked(path: str, scope: list[str]) -> bool:
    return any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in scope)


def git_tree(source: dict[str, Any], revision: str) -> dict[str, str]:
    data = fetch_json(github_api(source) + "/git/trees/" + revision + "?recursive=1")
    if data.get("truncated") is not False:
        raise ValueError("Git tree is incomplete; cannot close changed-file coverage")
    return {item["path"]: item["mode"] + ":" + item["sha"] for item in data["tree"]
            if item["type"] != "tree" and tracked(item["path"], source["tracked_paths"])}


def git_delta(source: dict[str, Any], before: str, after: str) -> list[dict[str, str]]:
    if before == after:
        return []
    old, new = git_tree(source, before), git_tree(source, after)
    return [{"path": path, "change": "added" if path not in old else "removed" if path not in new else "modified"}
            for path in sorted(old.keys() | new.keys()) if old.get(path) != new.get(path)]


def source_status(source: dict[str, Any], fetch: bool,
                  capture: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"id": source["id"], "kind": source["kind"], "role": source["role"],
                              "evidence": "cached", "checked_at": None,
                              "observed_at": source["observed"]["checked_at"],
                              "observed_revision": source["observed"]["revision"],
                              "reviewed_revision": source["reviewed_revision"],
                              "absorbed_revision": source["absorbed_revision"], "changes": [],
                              "change_coverage": "not_compared"}
    if source["kind"] == "git":
        if capture is not None:
            raise ValueError("document capture supplied for a Git source")
        if fetch:
            ref = fetch_json(github_api(source) + "/git/ref/heads/" + quote(source["branch"], safe="/"))
            revision = ref["object"]["sha"]
            if ref["object"]["type"] != "commit" or not SHA.fullmatch(revision):
                raise ValueError("branch did not resolve to a commit")
            result.update(evidence="live", checked_at=utc_now(), observed_revision=revision)
            result["observed_at"] = result["checked_at"]
        if not source["reviewed_revision"]:
            result.update(state="review_required", reason="tracked scope has not been completely reviewed")
            # Initial review remains pending; a later update can still be compared
            # against the recorded observation without calling it a reviewed baseline.
            baseline = source["observed"]["revision"]
            if fetch and baseline and baseline != result["observed_revision"]:
                result["changes"] = git_delta(source, baseline, result["observed_revision"])
                result.update(change_coverage="tracked_paths_since_observation", comparison_baseline=baseline)
        elif result["observed_revision"] != source["reviewed_revision"]:
            result["state"] = "review_required"
            if fetch:
                result["changes"] = git_delta(source, source["reviewed_revision"], result["observed_revision"])
                result.update(change_coverage="tracked_paths_since_review", comparison_baseline=source["reviewed_revision"])
                result["reason"] = "new revision requires disposition, including changes outside tracked paths"
        else:
            result["state"] = "current" if fetch else "cached"
            result["change_coverage"] = "same_recorded_revision"
    else:
        if capture is None:
            result.update(state="unavailable" if fetch else "review_required" if source["observed"]["revision"] != source["reviewed_revision"] else "cached",
                          reason="complete browser catalog capture required; use --snapshot (no login or challenge bypass)")
            return result
        snapshot = make_snapshot(capture, source)
        age = (datetime.now(timezone.utc) - timestamp(snapshot["captured_at"])).total_seconds()
        if age < -300:
            raise ValueError("capture timestamp is in the future")
        baseline = source["reviewed_snapshot"]
        result["changes"] = document_delta(baseline, snapshot)
        result.update(evidence="imported_snapshot", checked_at=utc_now(),
                      observed_at=snapshot["captured_at"], observed_revision=snapshot["revision"],
                      page_count=len(snapshot["pages"]), change_coverage="complete_catalog",
                      comparison_baseline=baseline["revision"])
        result["state"] = "review_required" if result["changes"] else "stale" if age > 86400 else "current"
        if age > 86400:
            result["reason"] = "capture older than 24 hours; not proof of current website content"
    if (result["state"] == "current" and source["reviewed_revision"]
            and source["observed"]["revision"] != source["reviewed_revision"]):
        result.update(state="review_required", pending_observed_revision=source["observed"]["revision"],
                      reason="recorded observation still needs disposition, even though the latest content reverted")
    return result


def validate_tracking(lock: dict[str, Any], root: Path) -> list[str]:
    """Validate the optional, versioned extension without rewriting legacy provenance."""
    errors = []
    registry = lock.get("reference_tracking")
    if registry is None:
        return errors
    try:
        if registry["schema"] != "money-craft.reference-tracking.v1":
            raise ValueError("unsupported reference tracking schema")
        seen = {item["id"] for item in lock["upstreams"]}
        for source in registry["sources"]:
            sid = source["id"]
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", sid) or sid in seen:
                raise ValueError("invalid or duplicate source id")
            seen.add(sid)
            public_url(source["url"])
            if source["kind"] not in {"git", "docs"} or source["role"] not in {"primary-reference", "adapter-candidate", "watchlist"}:
                raise ValueError("invalid source kind or role")
            if source["runtime_dependency"] is not False:
                raise ValueError("reference tracking does not authorize runtime dependencies")
            if not source["purpose"] or not source["license_status"]:
                raise ValueError("source purpose and license status are required")
            revision_pattern = SHA if source["kind"] == "git" else DIGEST
            timestamp(source["observed"]["checked_at"])
            for revision in (source["observed"]["revision"], source["reviewed_revision"], source["absorbed_revision"]):
                if revision is not None and not revision_pattern.fullmatch(revision):
                    raise ValueError("invalid immutable revision")
            if source["kind"] == "git":
                github_api(source)
                if not source["branch"] or source["branch"].startswith("/") or ".." in source["branch"]:
                    raise ValueError("invalid branch")
                if not source["tracked_paths"] or any(not isinstance(p, str) or not p or p.startswith("/") or ".." in p.split("/") for p in source["tracked_paths"]):
                    raise ValueError("tracked paths must be nonempty repository-relative scopes")
            else:
                snapshot = source["reviewed_snapshot"]
                if (snapshot["schema"] != SNAPSHOT_SCHEMA or snapshot["source_id"] != sid
                        or snapshot["normalizer"] != NORMALIZER or snapshot["catalog_complete"] is not True):
                    raise ValueError("invalid document snapshot identity or normalizer")
                timestamp(snapshot["captured_at"])
                urls = []
                for page in snapshot["pages"]:
                    url = public_url(page["url"])
                    if not in_docs(url, public_url(source["url"])) or not in_docs(public_url(page["final_url"]), public_url(source["url"])):
                        raise ValueError("snapshot page outside documentation scope")
                    if not DIGEST.fullmatch(page["sha256"]) or not page["title"]:
                        raise ValueError("invalid page hash or title")
                    urls.append(url)
                if not urls or len(set(urls)) != len(urls) or public_url(source["url"]) not in urls:
                    raise ValueError("invalid snapshot catalog")
                if snapshot_revision(snapshot["pages"]) != snapshot["revision"] or snapshot["revision"] != source["reviewed_revision"]:
                    raise ValueError("snapshot identity does not match reviewed revision")
            for decision in source["decisions"]:
                if decision["disposition"] not in {"adopt", "adapt", "defer", "reject"}:
                    raise ValueError("invalid absorption disposition")
                if not decision["reason"] or not decision["scope"] or not decision["targets"]:
                    raise ValueError("decision requires scope, rationale and target")
                if decision["disposition"] == "defer" and not decision.get("revisit_when"):
                    raise ValueError("deferred decision requires a revisit trigger")
                if decision["disposition"] in {"adopt", "adapt"} and (not decision.get("evidence") or not source["absorbed_revision"]):
                    raise ValueError("adoption requires an absorbed revision and validation evidence")
                for path in decision["targets"]:
                    target = (root / path.split("#")[0]).resolve()
                    if not target.is_relative_to(root.resolve()) or not target.is_file():
                        raise ValueError("decision target must exist inside the repository")
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        errors.append(f"reference tracking validation failed: {exc}")
    return errors
