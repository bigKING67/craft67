"""Local dated previews and evidence-driven catalyst replay; no external timestamp proof."""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import os
import tempfile
import re
from pathlib import Path

import earnings_update as eu


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()


def read(path):
    eu.require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 2 * 1024 * 1024,
               "expected regular JSON file <= 2 MiB")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise eu.EarningsError("invalid_preview", str(exc)) from exc


def calendar_today():
    # as_of/publication fields are civil dates; UTC instants remain UTC below.
    return dt.datetime.now().astimezone().date()


def validate(payload, base):
    eu.require(payload["schema"] == "money-craft.earnings-preview.v1", "unsupported preview schema")
    eu.require(eu.workflow.SECURITY_ID_RE.fullmatch(payload["security_id"]) is not None, "invalid security")
    eu.require(re.fullmatch(r"[A-Z]{3}", payload["currency"]) is not None, "invalid currency")
    sources = eu.validate_sources(payload, base)
    cutoff = eu.date(payload["as_of"], "preview as_of")
    eu.require(cutoff <= calendar_today(), "preview cannot be future dated")
    seen = set()
    eu.require(bool(payload["expectations"]), "at least one expectation required")
    for item in payload["expectations"]:
        identity = (item["metric"], item["origin"])
        eu.require(identity not in seen and item["metric"] in eu.METRICS, "duplicate or unsupported expectation")
        seen.add(identity)
        eu.require(item["origin"] in {"analyst", "management", "consensus"}, "expectation origin required")
        eu.require(bool(item["rationale"].strip()), "expectation rationale required")
        eu.require(eu.date(item["as_of"], "expectation date") <= cutoff, "expectation after preview")
        eu.validate_period_window({"start": item["period_start"], "end": item["period_end"],
                                   "kind": item["kind"], "accounting_basis": item["accounting_basis"]})
        eu.require(item["unit"] == ("shares" if item["metric"] == "shares" else payload["currency"]), "unit mismatch")
        eu.number(item["value"])
        eu.refs(item["source_refs"], sources)
        eu.require(all(sources[r["source_id"]]["published_on"] <= item["as_of"] for r in item["source_refs"]), "expectation uses future source")
    ids = set()
    for catalyst in payload["catalysts"]:
        eu.require(isinstance(catalyst["id"], str) and catalyst["id"].strip() and catalyst["id"] not in ids, "unique catalyst ID required")
        ids.add(catalyst["id"])
        eu.require(eu.date(catalyst["window_start"], "window start") <= eu.date(catalyst["window_end"], "window end"), "invalid window")
        for key in ("impact_path", "confirmation_condition", "invalidation_condition", "next_evidence", "decision_condition"):
            eu.require(isinstance(catalyst[key], str) and bool(catalyst[key].strip()), f"catalyst {key} required")
        eu.refs(catalyst["source_refs"], sources)
    return payload


def validate_linked_models(preview, directory):
    linked = preview.get("linked_model_hashes", {})
    eu.require(isinstance(linked, dict), "linked model hashes must be an object")
    for name, expected in linked.items():
        eu.require(name in {"model-input.json", "model-result.json"}, "unsupported linked model artifact")
        artifact = directory / name
        eu.require(artifact.is_file() and not artifact.is_symlink() and eu.digest(artifact) == expected, "linked model hash mismatch")


def seal(input_path, output_path):
    try:
        payload = validate(read(input_path), input_path.parent)
        validate_linked_models(payload, output_path.parent)
        payload = copy.deepcopy(payload)
        for source in payload["sources"].values():
            path = Path(source["local_path"])
            source["local_path"] = str(path if path.is_absolute() else (input_path.parent / path).absolute())
        body = {"schema": "money-craft.earnings-baseline.v1", "sealed_at": dt.datetime.now().astimezone().isoformat(), "preview": payload}
        result = {**body, "sha256": hashlib.sha256(encoded(body)).hexdigest()}
        # Publish a complete file atomically without replacing any prior version.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", dir=output_path.parent, prefix=".preview-", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(encoded(result) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary, output_path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return {"valid": True, "baseline": str(output_path), "sha256": result["sha256"], "sealed_at": body["sealed_at"],
                "timestamp_assurance": "LOCAL_CLOCK_ONLY"}
    except (KeyError, TypeError, AttributeError, ValueError, OSError, ArithmeticError) as exc:
        raise eu.EarningsError("invalid_preview", str(exc)) from exc


def load_baseline(path):
    sealed = read(path)
    body = {k: v for k, v in sealed.items() if k != "sha256"}
    eu.require(sealed["schema"] == "money-craft.earnings-baseline.v1" and hashlib.sha256(encoded(body)).hexdigest() == sealed["sha256"], "baseline integrity mismatch")
    validate(sealed["preview"], path.parent)
    validate_linked_models(sealed["preview"], path.parent)
    timestamp = dt.datetime.fromisoformat(sealed["sealed_at"])
    eu.require(timestamp.tzinfo is not None and timestamp <= dt.datetime.now(dt.timezone.utc), "invalid local seal timestamp")
    return sealed


def inspect_baseline(path):
    try:
        sealed = load_baseline(path)
        preview = sealed["preview"]
        today = calendar_today().isoformat()
        return {"schema": "money-craft.earnings-baseline-status.v1", "valid": True,
                "security_id": preview["security_id"], "baseline_sha256": sealed["sha256"],
                "sealed_at": sealed["sealed_at"], "as_of": preview["as_of"], "assessed_on": today,
                "file_integrity": "VERIFIED", "claim_support": "UNVERIFIED",
                "actual_disclosure_status": "UNVERIFIED_NO_OUTCOME_PROVIDED",
                "timestamp_assurance": "LOCAL_CLOCK_ONLY",
                "expectation_count": len(preview["expectations"]),
                "research_tasks": [{"catalyst_id": c["id"],
                    "state": "OVERDUE_UNVERIFIED" if today > c["window_end"] else "PENDING",
                    "why": c["impact_path"], "evidence_needed": c["next_evidence"],
                    "decision_condition": c["decision_condition"]} for c in preview["catalysts"]]}
    except (KeyError, TypeError, AttributeError, ValueError, OSError, ArithmeticError) as exc:
        raise eu.EarningsError("invalid_preview", str(exc)) from exc


def replay(baseline_path, outcome_path):
    try:
        sealed, outcome = load_baseline(baseline_path), read(outcome_path)
        preview = sealed["preview"]
        eu.require(outcome["schema"] == "money-craft.earnings-outcome.v1", "unsupported outcome schema")
        eu.require(outcome["security_id"] == preview["security_id"] and outcome["currency"] == preview["currency"], "outcome identity differs")
        eu.require(eu.date(outcome["as_of"], "outcome date") >= eu.date(preview["as_of"], "preview date"), "outcome predates baseline")
        sources = eu.validate_sources(outcome, outcome_path.parent)
        eu.require(eu.date(outcome["as_of"], "outcome date") <= calendar_today(), "outcome cannot be future dated")
        actual = outcome["actual"]
        eu.require(actual["basis"] == "reported", "restated actuals need an explicitly reconciled preview comparison")
        values = eu.period(actual, outcome["currency"], sources)
        event = outcome["first_actual_disclosure"]
        disclosed = eu.date(event["date"], "first disclosure")
        eu.refs(event["source_refs"], sources)
        eu.require(eu.date(actual["end"], "period end") <= disclosed <= eu.date(outcome["as_of"], "outcome date"), "invalid disclosure date")
        eu.require(any(sources[r["source_id"]]["published_on"] == event["date"] for r in event["source_refs"])
                   and all(sources[r["source_id"]]["published_on"] <= event["date"] for r in event["source_refs"]), "disclosure needs contemporaneous evidence")
        eu.require(all(disclosed <= eu.date(sources[r["source_id"]]["published_on"], "actual source") for item in actual["metrics"].values() for r in item["source_refs"]), "actual source precedes claimed first disclosure")
        eu.require(eu.date(preview["as_of"], "preview date") < disclosed, "preview must predate disclosure")
        timestamp = dt.datetime.fromisoformat(sealed["sealed_at"])
        eu.require(timestamp.tzinfo is not None and timestamp <= dt.datetime.now(dt.timezone.utc), "invalid local seal timestamp")
        comparisons = []
        for item in preview["expectations"]:
            eu.require(all(item[a] == actual[b] for a, b in (("period_start", "start"), ("period_end", "end"), ("kind", "kind"), ("accounting_basis", "accounting_basis"))), "expectation/actual fiscal basis differs")
            eu.require(item["unit"] == actual["metrics"][item["metric"]]["unit"], "actual unit differs")
            comparisons.append({"baseline": item, "actual_vs_expected": eu.delta(eu.number(item["value"]), values[item["metric"]])})
        observations = outcome["catalyst_observations"]
        eu.require(isinstance(observations, dict) and set(observations) <= {c["id"] for c in preview["catalysts"]}, "unknown catalyst observation")
        catalysts, tasks = [], []
        for catalyst in preview["catalysts"]:
            observation = observations.get(catalyst["id"])
            state, support = "PENDING", "UNVERIFIED"
            if observation is not None:
                eu.require(observation["state"] in {"OCCURRED", "CANCELLED"}, "unsupported event state")
                eu.require(preview["as_of"] <= observation["observed_on"] <= outcome["as_of"], "observation outside replay window")
                eu.date(observation["observed_on"], "observation date")
                eu.refs(observation["source_refs"], sources)
                eu.require(all(sources[r["source_id"]]["published_on"] <= observation["observed_on"] for r in observation["source_refs"]), "observation uses future evidence")
                eu.require(bool(observation["rationale"].strip()), "event interpretation rationale required")
                state = observation["state"]
                # An observed event never automatically confirms a thesis.
            elif outcome["as_of"] > catalyst["window_end"]:
                state = "OVERDUE_UNVERIFIED"
            catalysts.append({"baseline": catalyst, "state": state, "thesis_support": support, "observation": observation})
            tasks.append({"catalyst_id": catalyst["id"], "why": f"{state}: {catalyst['impact_path']}",
                          "evidence_needed": catalyst["next_evidence"], "decision_condition": catalyst["decision_condition"],
                          "status": "OPEN_REQUIRES_REVIEW"})
        return {"schema": "money-craft.earnings-replay.v1", "valid": True, "security_id": preview["security_id"], "as_of": outcome["as_of"],
                "baseline_sha256": sealed["sha256"], "outcome_sha256": hashlib.sha256(encoded(outcome)).hexdigest(),
                "timing": "LOCAL_SEALED_BEFORE_DISCLOSURE" if timestamp.date() < disclosed else "RECONSTRUCTED_AFTER_DISCLOSURE",
                "timestamp_assurance": "LOCAL_CLOCK_ONLY", "claim_support": "UNVERIFIED", "comparisons": comparisons,
                "catalysts": catalysts, "research_tasks": tasks, "automatic_thesis_update": False}
    except (KeyError, TypeError, AttributeError, ValueError, OSError, ArithmeticError) as exc:
        raise eu.EarningsError("invalid_preview", str(exc)) from exc
