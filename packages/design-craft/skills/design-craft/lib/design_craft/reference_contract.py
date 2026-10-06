"""Portable visual-reference contracts, validation, and pack construction."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import urlparse


CARD_SCHEMA = "design-craft.visual-reference-card.v1"
CATALOG_SCHEMA = "design-craft.visual-reference-catalog.v1"
PACK_SCHEMA = "design-craft.visual-reference-pack.v1"

CARD_STATUSES = (
    "candidate",
    "reviewed",
    "exemplar_only",
    "rejected",
    "stale",
    "unavailable",
    "project_validated",
)
HYPOTHESIS_STATUSES = (
    "proposed",
    "insufficient_evidence",
    "project_validated",
    "comparative_validated",
    "absorbed",
    "rejected",
)
EVIDENCE_STATUSES = ("observed", "partial", "unverified", "unavailable")
EVIDENCE_FACETS = (
    "desktop",
    "mobile",
    "origin_live",
    "interaction",
    "accessibility",
    "performance",
)
REFERENCE_ROLES = (
    "structure",
    "responsive",
    "tone",
    "interaction",
    "counter_reference",
)
SURFACE_MODES = ("Persuade", "Operate", "Read", "Experience")

CARD_KEYS = {
    "schema",
    "id",
    "status",
    "source",
    "origin",
    "classification",
    "evidence",
    "observations",
    "transferable_mechanisms",
    "do_not_copy",
    "not_suitable_when",
    "project_validation_refs",
    "rights",
    "lifecycle",
}
CATALOG_KEYS = {
    "schema",
    "id",
    "title",
    "observed_at",
    "source_policy",
    "cards",
    "hypotheses",
}
PACK_KEYS = {
    "schema",
    "status",
    "task",
    "references",
    "blocking_reasons",
    "created_at",
}

ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise ValueError(f"duplicate JSON key: {key}")
        payload[key] = value
    return payload


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object
    )
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _object(value: Any, path: str, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return None
    return value


def _exact_keys(
    value: dict[str, Any], expected: set[str], path: str, errors: list[str]
) -> None:
    missing = sorted(expected - set(value))
    extra = sorted(set(value) - expected)
    if missing or extra:
        errors.append(f"{path} keys mismatch missing={missing} extra={extra}")


def _string(
    value: Any,
    path: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
    max_length: int | None = None,
) -> str | None:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        errors.append(f"{path} must be a non-empty string")
        return None
    if max_length is not None and len(value) > max_length:
        errors.append(f"{path} must be at most {max_length} characters")
    return value


def _string_list(
    value: Any,
    path: str,
    errors: list[str],
    *,
    allowed: Iterable[str] | None = None,
    minimum: int = 0,
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{path}[{index}] must be a non-empty string")
            continue
        result.append(item)
    if len(result) != len(set(result)):
        errors.append(f"{path} must not contain duplicates")
    if len(result) < minimum:
        errors.append(f"{path} must contain at least {minimum} item(s)")
    if allowed is not None:
        invalid = sorted(set(result) - set(allowed))
        if invalid:
            errors.append(f"{path} contains unsupported values: {invalid}")
    return result


def _date(value: Any, path: str, errors: list[str], *, nullable: bool = False) -> date | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str):
        errors.append(f"{path} must be an ISO date")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path} must be an ISO date")
        return None


def _date_time(value: Any, path: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"{path} must be an ISO date-time")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{path} must be an ISO date-time")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{path} must include a timezone")
    return parsed


def _url(value: Any, path: str, errors: list[str], *, https_only: bool = False) -> str | None:
    raw = _string(value, path, errors)
    if raw is None:
        return None
    parsed = urlparse(raw)
    schemes = {"https"} if https_only else {"http", "https"}
    if parsed.scheme not in schemes or not parsed.netloc or parsed.username or parsed.password:
        errors.append(f"{path} must be a credential-free {'HTTPS' if https_only else 'HTTP(S)'} URL")
    return raw


def _validate_rights(
    value: Any, path: str, errors: list[str]
) -> dict[str, Any] | None:
    rights = _object(value, path, errors)
    if rights is None:
        return None
    expected = {
        "mode",
        "ai_training",
        "assets_redistributed",
        "policy_url",
        "policy_observed_at",
    }
    _exact_keys(rights, expected, path, errors)
    if rights.get("mode") != "reference-only":
        errors.append(f"{path}.mode must be reference-only")
    if rights.get("ai_training") is not False:
        errors.append(f"{path}.ai_training must be false")
    if rights.get("assets_redistributed") is not False:
        errors.append(f"{path}.assets_redistributed must be false")
    _url(rights.get("policy_url"), f"{path}.policy_url", errors, https_only=True)
    _date(rights.get("policy_observed_at"), f"{path}.policy_observed_at", errors)
    return rights


def validate_card(
    payload: Any, *, today: date | None = None
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    card = _object(payload, "card", errors)
    if card is None:
        return errors, warnings
    _exact_keys(card, CARD_KEYS, "card", errors)
    if card.get("schema") != CARD_SCHEMA:
        errors.append(f"card.schema must be {CARD_SCHEMA}")
    card_id = _string(card.get("id"), "card.id", errors)
    if card_id is not None and not ID_PATTERN.fullmatch(card_id):
        errors.append("card.id must use lowercase path-safe characters")
    status = card.get("status")
    if status not in CARD_STATUSES:
        errors.append(f"card.status must be one of {list(CARD_STATUSES)}")

    source = _object(card.get("source"), "card.source", errors)
    if source is not None:
        _exact_keys(
            source,
            {"provider", "issue_date", "post_url", "observed_at", "source_sha256"},
            "card.source",
            errors,
        )
        _string(source.get("provider"), "card.source.provider", errors)
        _date(source.get("issue_date"), "card.source.issue_date", errors)
        _url(source.get("post_url"), "card.source.post_url", errors, https_only=True)
        _date(source.get("observed_at"), "card.source.observed_at", errors)
        source_sha = _string(source.get("source_sha256"), "card.source.source_sha256", errors)
        if source_sha is not None and not SHA256_PATTERN.fullmatch(source_sha):
            errors.append("card.source.source_sha256 must be a lowercase SHA-256 digest")

    origin = _object(card.get("origin"), "card.origin", errors)
    if origin is not None:
        allowed_origin_keys = {"url", "domain", "title", "source_description"}
        missing_origin = {"url", "domain", "title"} - set(origin)
        extra_origin = set(origin) - allowed_origin_keys
        if missing_origin or extra_origin:
            errors.append(
                "card.origin keys mismatch "
                f"missing={sorted(missing_origin)} extra={sorted(extra_origin)}"
            )
        origin_url = _url(origin.get("url"), "card.origin.url", errors)
        domain = _string(origin.get("domain"), "card.origin.domain", errors)
        _string(origin.get("title"), "card.origin.title", errors)
        if "source_description" in origin:
            _string(
                origin.get("source_description"),
                "card.origin.source_description",
                errors,
                allow_empty=True,
                max_length=1000,
            )
        if origin_url and domain and urlparse(origin_url).hostname != domain.lower():
            errors.append("card.origin.domain must match card.origin.url hostname")

    classification = _object(card.get("classification"), "card.classification", errors)
    reference_roles: list[str] = []
    recommended_modes: list[str] = []
    blocked_modes: list[str] = []
    if classification is not None:
        _exact_keys(
            classification,
            {
                "source_surface",
                "product_archetype",
                "reference_roles",
                "recommended_surface_modes",
                "blocked_surface_modes",
            },
            "card.classification",
            errors,
        )
        _string(classification.get("source_surface"), "card.classification.source_surface", errors)
        _string(
            classification.get("product_archetype"),
            "card.classification.product_archetype",
            errors,
        )
        reference_roles = _string_list(
            classification.get("reference_roles"),
            "card.classification.reference_roles",
            errors,
            allowed=REFERENCE_ROLES,
        )
        recommended_modes = _string_list(
            classification.get("recommended_surface_modes"),
            "card.classification.recommended_surface_modes",
            errors,
            allowed=SURFACE_MODES,
        )
        blocked_modes = _string_list(
            classification.get("blocked_surface_modes"),
            "card.classification.blocked_surface_modes",
            errors,
            allowed=SURFACE_MODES,
        )
        overlap = sorted(set(recommended_modes).intersection(blocked_modes))
        if overlap:
            errors.append(f"card.classification surface modes overlap: {overlap}")

    evidence = _object(card.get("evidence"), "card.evidence", errors)
    evidence_statuses: dict[str, str] = {}
    if evidence is not None:
        _exact_keys(evidence, set(EVIDENCE_FACETS), "card.evidence", errors)
        for facet in EVIDENCE_FACETS:
            facet_payload = _object(evidence.get(facet), f"card.evidence.{facet}", errors)
            if facet_payload is None:
                continue
            _exact_keys(
                facet_payload,
                {"status", "evidence_refs", "notes"},
                f"card.evidence.{facet}",
                errors,
            )
            facet_status = facet_payload.get("status")
            if facet_status not in EVIDENCE_STATUSES:
                errors.append(
                    f"card.evidence.{facet}.status must be one of {list(EVIDENCE_STATUSES)}"
                )
            elif isinstance(facet_status, str):
                evidence_statuses[facet] = facet_status
            refs = _string_list(
                facet_payload.get("evidence_refs"),
                f"card.evidence.{facet}.evidence_refs",
                errors,
            )
            _string(
                facet_payload.get("notes"),
                f"card.evidence.{facet}.notes",
                errors,
                allow_empty=True,
            )
            if facet_status in {"observed", "partial"} and not refs:
                errors.append(
                    f"card.evidence.{facet}.evidence_refs must identify observed evidence"
                )

    observations = _string_list(card.get("observations"), "card.observations", errors)
    transferable = _string_list(
        card.get("transferable_mechanisms"), "card.transferable_mechanisms", errors
    )
    do_not_copy = _string_list(card.get("do_not_copy"), "card.do_not_copy", errors)
    unsuitable = _string_list(
        card.get("not_suitable_when"), "card.not_suitable_when", errors
    )
    project_refs = _string_list(
        card.get("project_validation_refs"), "card.project_validation_refs", errors
    )
    _validate_rights(card.get("rights"), "card.rights", errors)

    lifecycle = _object(card.get("lifecycle"), "card.lifecycle", errors)
    reviewed_at: date | None = None
    review_after: date | None = None
    if lifecycle is not None:
        _exact_keys(
            lifecycle, {"reviewed_at", "review_after"}, "card.lifecycle", errors
        )
        reviewed_at = _date(
            lifecycle.get("reviewed_at"),
            "card.lifecycle.reviewed_at",
            errors,
            nullable=True,
        )
        review_after = _date(
            lifecycle.get("review_after"),
            "card.lifecycle.review_after",
            errors,
            nullable=True,
        )
        if reviewed_at and review_after and review_after < reviewed_at:
            errors.append("card.lifecycle.review_after must not precede reviewed_at")
        if today and review_after and review_after < today and status != "stale":
            warnings.append(
                f"card {card_id or '<unknown>'} passed review_after and should be stale"
            )

    reviewed_statuses = {
        "reviewed",
        "exemplar_only",
        "rejected",
        "stale",
        "project_validated",
    }
    if status in reviewed_statuses:
        if not observations:
            errors.append("reviewed card must contain observations")
        if status != "rejected" and not transferable:
            errors.append("reviewed non-rejected card must contain transferable_mechanisms")
        if not do_not_copy:
            errors.append("reviewed card must contain do_not_copy")
        if not unsuitable:
            errors.append("reviewed card must contain not_suitable_when")
        if not reference_roles:
            errors.append("reviewed card must declare at least one reference role")
        if not recommended_modes and status not in {"rejected", "exemplar_only"}:
            errors.append("reviewed card must recommend at least one surface mode")
        if evidence_statuses.get("desktop") not in {"observed", "partial"}:
            errors.append("reviewed card requires desktop evidence")
        if evidence_statuses.get("mobile") not in {"observed", "partial"}:
            errors.append("reviewed card requires mobile evidence")
        if reviewed_at is None or review_after is None:
            errors.append("reviewed card requires lifecycle dates")
    if status == "project_validated" and not project_refs:
        errors.append("project_validated card requires project_validation_refs")
    if status == "candidate" and project_refs:
        errors.append("candidate card must not claim project validation")
    return errors, warnings


def validate_catalog(
    payload: Any, *, today: date | None = None
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    catalog = _object(payload, "catalog", errors)
    if catalog is None:
        return errors, warnings
    _exact_keys(catalog, CATALOG_KEYS, "catalog", errors)
    if catalog.get("schema") != CATALOG_SCHEMA:
        errors.append(f"catalog.schema must be {CATALOG_SCHEMA}")
    catalog_id = _string(catalog.get("id"), "catalog.id", errors)
    if catalog_id is not None and not ID_PATTERN.fullmatch(catalog_id):
        errors.append("catalog.id must use lowercase path-safe characters")
    _string(catalog.get("title"), "catalog.title", errors)
    _date(catalog.get("observed_at"), "catalog.observed_at", errors)
    _validate_rights(catalog.get("source_policy"), "catalog.source_policy", errors)

    cards_value = catalog.get("cards")
    cards: list[dict[str, Any]] = []
    if not isinstance(cards_value, list):
        errors.append("catalog.cards must be an array")
    else:
        for index, card in enumerate(cards_value):
            if isinstance(card, dict):
                cards.append(card)
            card_errors, card_warnings = validate_card(card, today=today)
            errors.extend(f"catalog.cards[{index}]: {error}" for error in card_errors)
            warnings.extend(f"catalog.cards[{index}]: {warning}" for warning in card_warnings)
    card_ids = [card.get("id") for card in cards if isinstance(card.get("id"), str)]
    if len(card_ids) != len(set(card_ids)):
        errors.append("catalog.cards must have unique ids")
    cards_by_id = {str(card["id"]): card for card in cards if isinstance(card.get("id"), str)}

    hypotheses = catalog.get("hypotheses")
    if not isinstance(hypotheses, list):
        errors.append("catalog.hypotheses must be an array")
        return errors, warnings
    hypothesis_ids: list[str] = []
    for index, item in enumerate(hypotheses):
        path = f"catalog.hypotheses[{index}]"
        hypothesis = _object(item, path, errors)
        if hypothesis is None:
            continue
        expected = {
            "id",
            "mechanism",
            "supporting_card_ids",
            "unique_origin_urls",
            "disconfirming_evidence",
            "origin_audit_refs",
            "target_validation_refs",
            "comparative_eval_refs",
            "status",
        }
        _exact_keys(hypothesis, expected, path, errors)
        hypothesis_id = _string(hypothesis.get("id"), f"{path}.id", errors)
        if hypothesis_id:
            hypothesis_ids.append(hypothesis_id)
            if not ID_PATTERN.fullmatch(hypothesis_id):
                errors.append(f"{path}.id must use lowercase path-safe characters")
        _string(hypothesis.get("mechanism"), f"{path}.mechanism", errors)
        supporting = _string_list(
            hypothesis.get("supporting_card_ids"), f"{path}.supporting_card_ids", errors
        )
        urls = _string_list(
            hypothesis.get("unique_origin_urls"), f"{path}.unique_origin_urls", errors
        )
        for url_index, url in enumerate(urls):
            _url(url, f"{path}.unique_origin_urls[{url_index}]", errors)
        _string_list(
            hypothesis.get("disconfirming_evidence"),
            f"{path}.disconfirming_evidence",
            errors,
        )
        origin_refs = _string_list(
            hypothesis.get("origin_audit_refs"), f"{path}.origin_audit_refs", errors
        )
        target_refs = _string_list(
            hypothesis.get("target_validation_refs"),
            f"{path}.target_validation_refs",
            errors,
        )
        comparative_refs = _string_list(
            hypothesis.get("comparative_eval_refs"),
            f"{path}.comparative_eval_refs",
            errors,
        )
        status = hypothesis.get("status")
        if status not in HYPOTHESIS_STATUSES:
            errors.append(f"{path}.status must be one of {list(HYPOTHESIS_STATUSES)}")

        missing_cards = sorted(set(supporting) - set(cards_by_id))
        if missing_cards:
            errors.append(f"{path} references missing cards: {missing_cards}")
        supporting_cards = [cards_by_id[card_id] for card_id in supporting if card_id in cards_by_id]
        expected_urls = sorted(
            {
                str(card.get("origin", {}).get("url"))
                for card in supporting_cards
                if isinstance(card.get("origin"), dict)
                and isinstance(card["origin"].get("url"), str)
            }
        )
        if urls != expected_urls:
            errors.append(f"{path}.unique_origin_urls must equal sorted supporting origins")
        promotable = {
            "proposed",
            "project_validated",
            "comparative_validated",
            "absorbed",
        }
        if status in promotable:
            if len(expected_urls) < 3:
                errors.append(f"{path} requires at least three unique origins")
            invalid_support = [
                card.get("id")
                for card in supporting_cards
                if card.get("status") not in {"reviewed", "project_validated"}
            ]
            if invalid_support:
                errors.append(f"{path} has non-reviewed supporting cards: {invalid_support}")
        if status in {"project_validated", "comparative_validated", "absorbed"} and not target_refs:
            errors.append(f"{path} requires target_validation_refs")
        if status in {"comparative_validated", "absorbed"} and not comparative_refs:
            errors.append(f"{path} requires comparative_eval_refs")
        reused_refs = sorted(set(target_refs) & set(comparative_refs))
        if reused_refs:
            errors.append(
                f"{path} must not reuse evidence across target_validation_refs "
                f"and comparative_eval_refs: {reused_refs}"
            )
        if status == "absorbed" and not origin_refs:
            errors.append(f"{path} requires origin_audit_refs")
    if len(hypothesis_ids) != len(set(hypothesis_ids)):
        errors.append("catalog.hypotheses must have unique ids")
    return errors, warnings


def validate_pack(payload: Any) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    pack = _object(payload, "pack", errors)
    if pack is None:
        return errors, warnings
    _exact_keys(pack, PACK_KEYS, "pack", errors)
    if pack.get("schema") != PACK_SCHEMA:
        errors.append(f"pack.schema must be {PACK_SCHEMA}")
    status = pack.get("status")
    if status not in {"ready", "incomplete"}:
        errors.append("pack.status must be ready or incomplete")
    task = _object(pack.get("task"), "pack.task", errors)
    if task is not None:
        _exact_keys(
            task,
            {"surface_mode", "audience", "primary_job", "authority_refs"},
            "pack.task",
            errors,
        )
        if task.get("surface_mode") not in SURFACE_MODES:
            errors.append(f"pack.task.surface_mode must be one of {list(SURFACE_MODES)}")
        _string(task.get("audience"), "pack.task.audience", errors)
        _string(task.get("primary_job"), "pack.task.primary_job", errors)
        _string_list(
            task.get("authority_refs"), "pack.task.authority_refs", errors, minimum=1
        )

    references = pack.get("references")
    card_ids: list[str] = []
    positive_count = 0
    if not isinstance(references, list):
        errors.append("pack.references must be an array")
    else:
        if len(references) > 3:
            errors.append("pack.references must contain no more than three items")
        if status == "ready" and not references:
            errors.append("ready pack must contain at least one reference")
        for index, item in enumerate(references):
            path = f"pack.references[{index}]"
            reference = _object(item, path, errors)
            if reference is None:
                continue
            _exact_keys(reference, {"card_id", "role", "adapt", "reject", "unverified"}, path, errors)
            card_id = _string(reference.get("card_id"), f"{path}.card_id", errors)
            if card_id:
                card_ids.append(card_id)
            role = reference.get("role")
            if role not in REFERENCE_ROLES:
                errors.append(f"{path}.role must be one of {list(REFERENCE_ROLES)}")
            elif role != "counter_reference":
                positive_count += 1
            _string_list(reference.get("adapt"), f"{path}.adapt", errors)
            _string_list(reference.get("reject"), f"{path}.reject", errors)
            _string_list(reference.get("unverified"), f"{path}.unverified", errors)
    if len(card_ids) != len(set(card_ids)):
        errors.append("pack.references must not repeat cards")
    if references and positive_count == 0:
        errors.append("pack requires at least one positive reference")
    blockers = _string_list(pack.get("blocking_reasons"), "pack.blocking_reasons", errors)
    if status == "ready" and blockers:
        errors.append("ready pack must not contain blocking_reasons")
    if status == "incomplete" and not blockers:
        errors.append("incomplete pack must contain blocking_reasons")
    _date_time(pack.get("created_at"), "pack.created_at", errors)
    return errors, warnings


def validate_document(
    payload: Any, *, today: date | None = None
) -> tuple[str, list[str], list[str]]:
    if not isinstance(payload, dict):
        return "unknown", ["document must be an object"], []
    schema = payload.get("schema")
    if schema == CARD_SCHEMA:
        errors, warnings = validate_card(payload, today=today)
    elif schema == CATALOG_SCHEMA:
        errors, warnings = validate_catalog(payload, today=today)
    elif schema == PACK_SCHEMA:
        errors, warnings = validate_pack(payload)
    else:
        return str(schema or "unknown"), [f"unsupported schema: {schema!r}"], []
    return str(schema), errors, warnings


def build_reference_pack(
    catalog: dict[str, Any],
    selections: Sequence[tuple[str, str]],
    *,
    surface_mode: str,
    audience: str,
    primary_job: str,
    authority_refs: Sequence[str],
    created_at: str | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    catalog_errors, _ = validate_catalog(catalog)
    if catalog_errors:
        blockers.extend(f"invalid catalog: {error}" for error in catalog_errors)
    if surface_mode not in SURFACE_MODES:
        blockers.append(f"unsupported surface mode: {surface_mode}")
    if not audience.strip():
        blockers.append("audience is required")
    if not primary_job.strip():
        blockers.append("primary_job is required")
    if not authority_refs:
        blockers.append("at least one authority reference is required")
    if not 1 <= len(selections) <= 3:
        blockers.append("select between one and three references")

    # Never project card fields from a catalog that failed the trust-boundary
    # validation above. The diagnostic Pack remains contract-valid and exposes
    # the catalog errors through blocking_reasons instead of raising on malformed
    # nested values.
    cards = (
        catalog.get("cards")
        if not catalog_errors and isinstance(catalog.get("cards"), list)
        else []
    )
    cards_by_id = {
        str(card["id"]): card
        for card in cards
        if isinstance(card, dict) and isinstance(card.get("id"), str)
    }
    seen_cards: set[str] = set()
    references: list[dict[str, Any]] = []
    positive_count = 0
    for card_id, role in selections[:3]:
        if card_id in seen_cards:
            blockers.append(f"duplicate reference card: {card_id}")
            continue
        seen_cards.add(card_id)
        if role not in REFERENCE_ROLES:
            blockers.append(f"unsupported reference role for {card_id}: {role}")
            continue
        card = cards_by_id.get(card_id)
        if card is None:
            blockers.append(f"reference card not found: {card_id}")
            continue
        card_status = card.get("status")
        counter = role == "counter_reference"
        allowed_statuses = (
            {"reviewed", "exemplar_only", "project_validated"}
            if counter
            else {"reviewed", "project_validated"}
        )
        if card_status not in allowed_statuses:
            blockers.append(f"{card_id} status {card_status!r} cannot be used as {role}")
        classification = card.get("classification", {})
        declared_roles = classification.get("reference_roles", [])
        recommended = classification.get("recommended_surface_modes", [])
        blocked = classification.get("blocked_surface_modes", [])
        if role not in declared_roles:
            blockers.append(f"{card_id} does not declare reference role {role}")
        if not counter:
            positive_count += 1
            if surface_mode in blocked:
                blockers.append(f"{card_id} explicitly blocks surface mode {surface_mode}")
            elif surface_mode not in recommended:
                blockers.append(f"{card_id} is not reviewed for surface mode {surface_mode}")
        evidence = card.get("evidence", {})
        if role == "interaction":
            for facet in ("origin_live", "interaction"):
                if evidence.get(facet, {}).get("status") != "observed":
                    blockers.append(
                        f"{card_id} interaction role requires observed {facet} evidence"
                    )
        unverified = [
            f"{facet}: {evidence.get(facet, {}).get('status', 'missing')}"
            for facet in EVIDENCE_FACETS
            if evidence.get(facet, {}).get("status") != "observed"
        ]
        transferable = list(card.get("transferable_mechanisms", []))
        reject = list(card.get("do_not_copy", [])) + list(card.get("not_suitable_when", []))
        references.append(
            {
                "card_id": card_id,
                "role": role,
                "adapt": [] if counter else transferable,
                "reject": list(dict.fromkeys(reject)),
                "unverified": unverified,
            }
        )
    if positive_count == 0:
        blockers.append("at least one positive reference is required")

    timestamp = created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    pack = {
        "schema": PACK_SCHEMA,
        "status": "incomplete" if blockers else "ready",
        "task": {
            "surface_mode": surface_mode,
            "audience": audience,
            "primary_job": primary_job,
            "authority_refs": list(dict.fromkeys(authority_refs)),
        },
        "references": references,
        "blocking_reasons": list(dict.fromkeys(blockers)),
        "created_at": timestamp,
    }
    return pack


def schema_contract_errors(contract_dir: Path) -> list[str]:
    errors: list[str] = []
    try:
        card = load_json(contract_dir / "visual-reference-card.schema.json")
        catalog = load_json(contract_dir / "visual-reference-catalog.schema.json")
        pack = load_json(contract_dir / "visual-reference-pack.schema.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"visual reference schema load failed: {exc}"]

    checks = [
        (
            card.get("properties", {}).get("schema", {}).get("const") == CARD_SCHEMA,
            "card schema id mismatch",
        ),
        (
            tuple(card.get("properties", {}).get("status", {}).get("enum", []))
            == CARD_STATUSES,
            "card status enum mismatch",
        ),
        (
            tuple(
                card.get("$defs", {})
                .get("evidenceFacet", {})
                .get("properties", {})
                .get("status", {})
                .get("enum", [])
            )
            == EVIDENCE_STATUSES,
            "evidence status enum mismatch",
        ),
        (
            set(card.get("required", [])) == CARD_KEYS,
            "card required keys mismatch",
        ),
        (
            catalog.get("properties", {}).get("schema", {}).get("const")
            == CATALOG_SCHEMA,
            "catalog schema id mismatch",
        ),
        (
            set(catalog.get("required", [])) == CATALOG_KEYS,
            "catalog required keys mismatch",
        ),
        (
            tuple(
                catalog.get("properties", {})
                .get("hypotheses", {})
                .get("items", {})
                .get("properties", {})
                .get("status", {})
                .get("enum", [])
            )
            == HYPOTHESIS_STATUSES,
            "hypothesis status enum mismatch",
        ),
        (
            pack.get("properties", {}).get("schema", {}).get("const") == PACK_SCHEMA,
            "pack schema id mismatch",
        ),
        (set(pack.get("required", [])) == PACK_KEYS, "pack required keys mismatch"),
        (
            tuple(
                pack.get("properties", {})
                .get("task", {})
                .get("properties", {})
                .get("surface_mode", {})
                .get("enum", [])
            )
            == SURFACE_MODES,
            "pack surface mode enum mismatch",
        ),
        (
            tuple(
                pack.get("properties", {})
                .get("references", {})
                .get("items", {})
                .get("properties", {})
                .get("role", {})
                .get("enum", [])
            )
            == REFERENCE_ROLES,
            "pack reference role enum mismatch",
        ),
    ]
    errors.extend(message for ok, message in checks if not ok)
    return errors
