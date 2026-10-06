"""Cross-check saved preview inputs against captured Fuyao income data.

A separate data channel corroborates numbers, not issuer-independent economics.
The explicit cumulative-basis declaration requires a human filing check.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import earnings_baseline as baseline
import earnings_update as eu

FIELDS = {"revenue": "operating_income", "net_income": "parent_holder_net_profit"}


def check_file(input_path: Path, baseline_path: Path):
    try:
        spec = baseline.read(input_path)
        sealed = baseline.load_baseline(baseline_path)
        preview = sealed["preview"]
        eu.require(spec["schema"] == "money-craft.earnings-crosscheck-input.v1", "unsupported crosscheck schema")
        eu.require(spec["security_id"] == preview["security_id"], "crosscheck security differs")
        as_of = eu.date(spec["as_of"], "crosscheck as_of")
        eu.require(eu.date(preview["as_of"], "preview date") <= as_of <= baseline.calendar_today(), "invalid crosscheck date")
        eu.require(isinstance(spec["checks"], list) and bool(spec["checks"]), "checks required")
        result = {"schema": "money-craft.earnings-crosscheck.v1", "valid": False, "security_id": preview["security_id"],
            "as_of": spec["as_of"], "baseline_sha256": sealed["sha256"], "input_sha256": eu.digest(input_path),
            "numeric_status": "MISSING", "checks": [], "provider_vintage": "CURRENT_SNAPSHOT_NOT_POINT_IN_TIME",
            "source_lineage": "SEPARATE_PROVIDER_CHANNEL_ISSUER_ORIGIN_NOT_INDEPENDENT", "claim_support": "UNVERIFIED",
            "research_readiness": "PARTIAL", "network_used": False}
        capture_path = spec.get("provider_capture")
        if not capture_path:
            return result
        folder = Path(capture_path)
        folder = folder if folder.is_absolute() else input_path.parent / folder
        capture = baseline.read(folder / "capture.json")
        raw_path = folder / "response.json"
        eu.require(raw_path.is_file() and not raw_path.is_symlink() and raw_path.stat().st_size <= 2 * 1024 * 1024, "invalid provider response file")
        eu.require(eu.digest(raw_path) == capture["response_sha256"], "provider capture hash mismatch")
        eu.require(capture["schema"] == "money-craft.source-capture.v1" and capture["provider"] == "fuyao"
                   and capture["operation"] == "financials.income", "wrong provider capture contract")
        fetched = dt.datetime.fromisoformat(capture["fetched_at"].replace("Z", "+00:00"))
        eu.require(fetched.tzinfo is not None and fetched <= dt.datetime.now(dt.timezone.utc) and fetched.astimezone(ZoneInfo("Asia/Shanghai")).date() <= as_of, "capture unavailable at crosscheck cutoff")
        raw = json.loads(raw_path.read_text(), parse_float=str)
        eu.require(raw["code"] == 0 and raw["request_id"] == capture["request_id"], "provider business error or request mismatch")
        result.update(provider_response_sha256=capture["response_sha256"], provider_fetched_at=capture["fetched_at"],
                      captured_after_baseline=fetched > dt.datetime.fromisoformat(sealed["sealed_at"]))
        if spec.get("provider_basis") != "ytd_confirmed_against_filing":
            result["numeric_status"] = "UNVERIFIED_BASIS"
            return result
        eu.require(spec["security_id"].startswith(("CN-SH:", "CN-SZ:")), "Fuyao crosscheck supports Shanghai/Shenzhen A shares")
        symbol = spec["security_id"].split(":")[1] + (".SH" if spec["security_id"].startswith("CN-SH:") else ".SZ")
        records = raw["data"]["item"]
        eu.require(isinstance(records, list), "invalid provider items")

        def extract(year, quarter, metric):
            rows = [r for r in records if r.get("fiscal_year") == year and r.get("fiscal_period") == f"Q{quarter}" and r.get("thscode") == symbol]
            if not rows:
                return None
            eu.require(len(rows) == 1, "ambiguous provider period")
            row = rows[0]
            eu.require(row["currency"] == preview["currency"] and row["period"] == "quarterly", "provider currency or frequency differs")
            end = dt.date(year, quarter * 3, 30 if quarter in (2, 3) else 31)
            observed_end = dt.datetime.fromtimestamp(row["period_end_ms"] / 1000, ZoneInfo("Asia/Shanghai")).date()
            publication = dt.datetime.fromtimestamp(row["report_date_ms"] / 1000, ZoneInfo("Asia/Shanghai")).date()
            eu.require(observed_end == end and end <= publication <= min(as_of, fetched.astimezone(ZoneInfo("Asia/Shanghai")).date()), "provider date/basis mismatch or future disclosure")
            value = row.get(FIELDS[metric])
            if value is None:
                return None
            eu.require(isinstance(value, (str, int)) and not isinstance(value, bool), "invalid provider numeric value")
            return eu.number(str(value))

        statuses, seen = [], set()
        for item in spec["checks"]:
            metric, year, quarter, kind = item["metric"], item["year"], item["quarter"], item["kind"]
            eu.require(metric in FIELDS and type(year) is int and 1900 <= year <= 2099 and type(quarter) is int and 1 <= quarter <= 4
                       and kind in {"ytd", "quarter"}, "unsupported check period or metric")
            identity = (metric, year, quarter, kind)
            eu.require(identity not in seen, "duplicate numeric check")
            seen.add(identity)
            eu.require(item["unit"] == preview["currency"], "primary unit differs")
            eu.refs(item["source_refs"], preview["sources"])
            end = dt.date(year, quarter * 3, 30 if quarter in (2, 3) else 31)
            eu.require(all(eu.date(preview["sources"][r["source_id"]]["published_on"], "filing publication") >= end for r in item["source_refs"]), "primary evidence predates actual period")
            primary = eu.number(item["value"])
            provider = extract(year, quarter, metric)
            operands = [str(provider)] if provider is not None else []
            if kind == "quarter" and quarter > 1:
                previous = extract(year, quarter - 1, metric)
                operands.append(str(previous) if previous is not None else None)
                provider = eu.finance.calculate("subtract", [provider, previous]) if provider is not None and previous is not None else None
            error = None
            if provider is None:
                status = "MISSING"
            else:
                difference = eu.finance.calculate("subtract", [primary, provider]).copy_abs()
                error = eu.finance.calculate("divide", [difference, max(primary.copy_abs(), Decimal("0.000001"))])
                status = "MATCHED" if error <= Decimal("0.01") else "REVIEW_REQUIRED" if error <= Decimal("0.05") else "CONFLICT"
            statuses.append(status)
            result["checks"].append({**item, "provider_value": str(provider) if provider is not None else None,
                "provider_ytd_operands": operands, "relative_difference": str(error) if error is not None else None, "status": status})
        result["numeric_status"] = next(s for s in ("CONFLICT", "REVIEW_REQUIRED", "MISSING", "MATCHED") if s in statuses)
        result["valid"] = result["numeric_status"] == "MATCHED"
        result["coverage_scope"] = "ONLY_DECLARED_CHECKS_NOT_ALL_BASELINE_DEPENDENCIES"
        return result
    except (KeyError, TypeError, AttributeError, ValueError, OSError, ArithmeticError) as exc:
        raise eu.EarningsError("invalid_crosscheck", str(exc)) from exc
