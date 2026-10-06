from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SemanticPaths:
    source_root: Path
    routing: Path
    route_plan: Path
    route_core: Path
    route_authority: Path
    route_browser: Path
    route_evidence: Path
    route_visual_review: Path
    route_browser_capture: Path
    route_browser_capture_sanitize: Path
    route_browser_capture_store: Path
    route_browser_contract: Path
    route_browser_receipt: Path
    route_browser_receipt_core: Path
    route_browser_receipt_reducer: Path
    route_delivery: Path
    route_runtime: Path
    route_telemetry: Path
    platform_detect: Path
    worker_entry: Path
    worker_route_core: Path
    worker_payload_core: Path
    worker_agent: Path
    config: Path

    @property
    def route_files(self) -> tuple[Path, ...]:
        return (
            self.route_plan,
            self.route_core,
            self.route_authority,
            self.route_browser,
            self.route_evidence,
            self.route_visual_review,
            self.route_browser_capture,
            self.route_browser_capture_sanitize,
            self.route_browser_capture_store,
            self.route_browser_contract,
            self.route_browser_receipt,
            self.route_browser_receipt_core,
            self.route_browser_receipt_reducer,
            self.route_delivery,
            self.route_runtime,
            self.route_telemetry,
            self.worker_entry,
            self.worker_route_core,
            self.worker_payload_core,
        )


def semantic_paths(source_root: Path) -> SemanticPaths:
    tools = source_root / "tools"
    return SemanticPaths(
        source_root=source_root,
        routing=tools / "frontend_agent_routing.json",
        route_plan=tools / "frontend_route_plan.sh",
        route_core=tools / "frontend_route_core.py",
        route_authority=tools / "frontend_route_authority.py",
        route_browser=tools / "frontend_route_browser.py",
        route_evidence=tools / "frontend_route_evidence.py",
        route_visual_review=tools / "frontend_route_visual_review.py",
        route_browser_capture=tools / "frontend_route_browser_capture.py",
        route_browser_capture_sanitize=(
            tools / "frontend_route_browser_capture_sanitize.py"
        ),
        route_browser_capture_store=(
            tools / "frontend_route_browser_capture_store.py"
        ),
        route_browser_contract=tools / "frontend_route_browser_contract.py",
        route_browser_receipt=tools / "frontend_route_browser_receipt.py",
        route_browser_receipt_core=(
            tools / "frontend_route_browser_receipt_core.py"
        ),
        route_browser_receipt_reducer=(
            tools / "frontend_route_browser_receipt_reducer.py"
        ),
        route_delivery=tools / "frontend_route_delivery.py",
        route_runtime=tools / "frontend_route_runtime.py",
        route_telemetry=tools / "frontend_route_telemetry.py",
        platform_detect=tools / "frontend_platform_detect.py",
        worker_entry=tools / "frontend_worker_entry.sh",
        worker_route_core=tools / "frontend_worker_route_core.py",
        worker_payload_core=tools / "frontend_worker_payload_core.py",
        worker_agent=source_root / "agents/worker.toml",
        config=source_root / "config.toml",
    )


STALE_FRAGMENTS = (
    "gpt-5.5",
    "default_high",
    "worker_xhigh",
    "route_defaults =",
)
EXPLICIT_REASONING_VOCABULARY = "auto|inherit|low|medium|high|xhigh|max"
REQUIRED_FRAGMENTS = {
    "frontend_route_plan.sh": (
        "frontend_route_core.py",
        "--orchestration",
        "--platform",
        "--product-context-path",
        "--browser-context",
        "--evidence-mode",
        "--delegation-authorization",
        "--visual-contract",
        "compact-json",
        "human",
    ),
    "frontend_route_core.py": (
        "from frontend_route_authority import",
        "from frontend_route_browser import resolve_browser_route",
        "from frontend_route_evidence import resolve_evidence_contract",
        "from frontend_route_delivery import",
        "from frontend_route_runtime import resolve_runtime_profile",
        "from frontend_route_telemetry import ROUTE_TELEMETRY_SCHEMA, append_route_event",
        "quality_governance",
        "delegation_contract",
        "runtime_profile_verified",
        "delegation_authorization_missing",
        "architecture_review_required_intents",
        "performance_review_required_for_surfaces",
        '"frontend-route.compact.v1"',
        '"design_tier": tier',
        '"preferred_browser_tool": preferred_browser_tool',
        '"planned_browser_lifecycle": planned_browser_lifecycle',
        '"actual_browser_lifecycle_state": actual_browser_lifecycle_state',
        '"runtime_validation_kind": runtime_validation_kind',
        '"native_validation_required": native_validation_required',
        '"evidence_mode": evidence_mode',
        '"evidence_contract": evidence_contract',
    ),
    "frontend_route_authority.py": (
        "discover_design_md",
        "authority_digest",
        "build_authority_constraints",
    ),
    "frontend_route_browser.py": (
        "resolve_browser_route",
        "evidence_mode",
        '"preferred_browser_tool"',
        '"native_validation_required"',
        '"planned_browser_lifecycle"',
        '"actual_browser_lifecycle_state"',
    ),
    "frontend_route_evidence.py": (
        "VALID_EVIDENCE_MODES",
        "resolve_evidence_contract",
        '"comp-fidelity"',
        '"sealed-rendition"',
        '"measurement_is_visual_acceptance"',
        '"global_pixel_pass_threshold"',
    ),
    "frontend_route_visual_review.py": (
        "resolve_visual_review_contract",
        "evidence_mode",
        'mode = "final_only"',
    ),
    "frontend_route_browser_capture.py": (
        "from frontend_route_browser_capture_sanitize import",
        "from frontend_route_browser_capture_store import",
        '"--ingest-hook"',
        '"--strict"',
        "MAX_HOOK_BYTES",
    ),
    "frontend_route_browser_capture_sanitize.py": (
        "def sanitize_route",
        "def sanitize_hook_event",
        "def _aliased_token",
        '"workspaceKey"',
        '"preferred_browser_tool": SOURCE_SERVER',
        "SUPPORTED_ACTIONS",
    ),
    "frontend_route_browser_capture_store.py": (
        'CAPTURE_STATE_FILE = "capture-state.json"',
        'CAPTURE_HEALTH_FILE = "capture-health.json"',
        'CAPTURE_STATUS_SCHEMA = "frontend-route.browser-capture-status.v2"',
        '"last_error_code"',
        '"error_count"',
        '"health_persisted"',
        '"health_status"',
        "MAX_INCOMPLETE_STATES = 1000",
        "MAX_COMPLETE_RECEIPTS = 100",
        "def save_route_binding",
        "def ingest_observation",
        "def prune_capture_state",
    ),
    "frontend_route_browser_contract.py": (
        'RECEIPT_SCHEMA = "frontend-route.browser-lifecycle-receipt.v2"',
        'OBSERVATIONS_SCHEMA = "frontend-route.browser-lifecycle-observations.v2"',
        'OUTCOME_SCHEMA = "browser67.tool-outcome.v3"',
        "MAX_ROUTE_BYTES",
        "MAX_OBSERVATIONS",
        "planner_actual_browser_lifecycle_state",
    ),
    "frontend_route_browser_receipt.py": (
        "from frontend_route_browser_receipt_core import",
        '"--require-complete"',
        "return 3",
    ),
    "frontend_route_browser_receipt_core.py": (
        "def read_json_file",
        "def normalize_receipt",
        '"receipt_valid"',
        '"runtime_complete"',
        '"host_observation_binding"',
    ),
    "frontend_route_browser_receipt_reducer.py": (
        "class LifecycleReducer",
        "def expected_scope",
        '"workspaceKey"',
        "def _apply_entry",
        "def _apply_inspection",
        "def _apply_adoption",
        "def _apply_finalize",
        "def format_delivery_summary",
    ),
    "frontend_route_delivery.py": (
        "build_skill_selection_contract",
        "build_delivery_contract",
        "current Codex turn_context",
        "planned_browser_lifecycle",
        "actual_browser_lifecycle_state",
    ),
    "frontend_route_runtime.py": (
        "FRONTEND_RUNTIME_SESSION_DISCOVERY",
        "codex_session_turn_context",
        "contains_prompt_data",
        "_safe_evidence_path",
        "resolve_runtime_profile",
    ),
    "frontend_route_telemetry.py": (
        "FRONTEND_ROUTE_TELEMETRY_LOG_ENABLED",
        "FRONTEND_ROUTE_TELEMETRY_CONTEXT",
        "append_route_event",
        "summarize",
        'EVENT_SCHEMA = "frontend-route.telemetry-event.v2"',
        'SUMMARY_SCHEMA = "frontend-route.telemetry-summary.v2"',
        '"p50"',
        '"p95"',
        '"contains_sensitive_data"',
    ),
    "frontend_worker_entry.sh": (
        "frontend_worker_route_core.py",
        "frontend_worker_payload_core.py",
        "--platform",
        "--runtime-validation-kind",
        "--preferred-runtime-tool",
    ),
    "frontend_worker_route_core.py": (
        "reasoning_targets",
        "delegation_policies",
        "runtime_remediation_policies",
        "validate_document",
    ),
    "frontend_worker_payload_core.py": (
        "runtime_validation_kinds",
        '"design_tier": frontend_tier',
        '"preferred_runtime_tool": preferred_runtime_tool',
    ),
}
