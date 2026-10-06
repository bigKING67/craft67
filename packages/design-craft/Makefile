DESIGN_CRAFT_SKILL_ROOT ?= $(HOME)/.agents/skills
SKILL_CREATOR_QUICK_VALIDATE ?=
INSTALL_ARGS ?=
BENCHMARK_BASELINE ?=
BENCHMARK_RESULT ?=
BENCHMARK_RUN_OBSERVATION ?=
RELEASE_ASSET_DIR ?= dist/release
RELEASE_EVIDENCE_DIR ?= dist/evidence
NATIVE_EVIDENCE_ROOT ?= $(DESIGN_CRAFT_NATIVE_EVIDENCE_ROOT)
CERTIFICATION_BUNDLE_DIR ?= dist/certification
CERTIFICATION_TAG ?= v$(shell cat VERSION)
CERTIFICATION_REPOSITORY ?=
CERTIFICATION_RUN_ID ?=
CERTIFICATION_RUN_ATTEMPT ?=
OPERATIONAL_CANDIDATE_EVIDENCE ?= $(RELEASE_EVIDENCE_DIR)/operational-95-candidate.json
OPERATIONAL_FINAL_EVIDENCE ?= $(RELEASE_EVIDENCE_DIR)/operational-95-final.json
CERTIFIED_CANDIDATE_EVIDENCE ?= $(RELEASE_EVIDENCE_DIR)/certified-100-candidate.json
CERTIFIED_FINAL_EVIDENCE ?= $(RELEASE_EVIDENCE_DIR)/certified-100-final.json
export PYTHONDONTWRITEBYTECODE := 1

.PHONY: validate validate-portable lint contract-tests package-check public-repo-check workflow-check skill-quick-validate score visual-reference-check shadow-lab-check comp-fidelity-check sealed-rendition-check \
	maturity-development maturity-operational maturity-certified pass audit critique prototype system-review motion primitive-selection motion-plan-dry-run taste-review \
	seed-dry-run route-smoke doctor platform-scan-check native-runtime-probe native-runtime-check native-release-bundle-check \
	native-release-bundle-build native-release-bundle-verify codex-route-pack-check codex-route-pack-host-check init-dry-run active-scope-check \
	cross-agent-check cross-agent-history-check cross-agent-observed-check cross-agent-four-host-check \
	cross-agent-motion-observed-check cross-agent-native-observed-check comparative-check comparative-history-check \
	comparative-observed-check history-audit l4-capture-check historical-l4-metadata-check real-l4-check smell-smoke static-review-smoke \
	upstream-report upstream-absorption-check taste-absorption-check impeccable-absorption-check emil-absorption-check jakub-absorption-check \
	upstream-freshness-audit upstream-remote-report sync-status-check sync-status sync-status-remote install install-verify \
	github-governance-contract-check github-governance-check github-governance-apply release-gate-source publish-local \
	release-readiness-operational release-tag-verify-operational release-assets-build-operational \
	release-assets-verify-operational release-final-verify-operational release-readiness-certified \
	release-tag-verify-certified release-assets-build-certified release-assets-verify-certified \
	release-final-verify-certified release-certification-build-operational \
	release-certification-verify-operational release-certification-build-certified \
	release-certification-verify-certified

validate:
	bash scripts/validate.sh

validate-portable:
	bash scripts/validate.sh --portable

lint:
	python3 scripts/design_craft_lint.py --check

contract-tests:
	python3 -m tools.design_craft validate --profile contracts

package-check:
	python3 scripts/design_craft_package_validate.py --check --validate

public-repo-check:
	python3 scripts/design_craft_public_repo_validate.py --check --validate

workflow-check:
	python3 scripts/design_craft_workflow_validate.py --check --validate

skill-quick-validate:
	python3 -m tools.design_craft.validation.skill_schema --check skills/design-craft
	@if [ -n "$(SKILL_CREATOR_QUICK_VALIDATE)" ]; then \
		python3 "$(SKILL_CREATOR_QUICK_VALIDATE)" skills/design-craft; \
	fi

score:
	python3 scripts/design_craft_score.py --self

shadow-lab-check:
	PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.unit.test_shadow_lab tests.unit.test_shadow_lab_comparison tests.integration.test_shadow_lab_cli tests.integration.test_shadow_compare_cli tests.adversarial.test_shadow_lab_boundaries

comp-fidelity-check:
	PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.unit.test_comp_fidelity tests.integration.test_comp_fidelity_cli
	PYTHONDONTWRITEBYTECODE=1 python3 skills/design-craft/scripts/design_craft_comp_fidelity.py --check >/dev/null

sealed-rendition-check:
	PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.unit.test_sealed_rendition tests.integration.test_sealed_rendition_cli
	PYTHONDONTWRITEBYTECODE=1 python3 skills/design-craft/scripts/design_craft_sealed_rendition_gate.py --check >/dev/null

visual-reference-check: shadow-lab-check comp-fidelity-check sealed-rendition-check
	PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.unit.test_visual_reference_contract tests.unit.test_visual_reference_target_fixture tests.unit.test_visual_reference_comparative_fixture tests.unit.test_peekpaper_adapter tests.unit.test_route_runtime tests.integration.test_visual_reference_cli
	PYTHONDONTWRITEBYTECODE=1 python3 skills/design-craft/scripts/design_craft_reference.py validate evals/visual-reference/peekpaper-pilot/catalog.json evals/visual-reference/golden/reference-transfer/expected.json evals/visual-reference/target-validation/reference-assisted-product-landing/reference-pack.json evals/visual-reference/comparative-validation/reference-assisted-evidence-dossier/reference-pack.json
	PYTHONDONTWRITEBYTECODE=1 python3 skills/design-craft/scripts/design_craft_reference.py validate evals/visual-reference/golden/beautiful-but-wrong/expected.json
	PYTHONDONTWRITEBYTECODE=1 python3 skills/design-craft/scripts/design_craft_l4_evidence_manifest.py --validate-screenshots-json evals/visual-reference/target-validation/reference-assisted-product-landing/screenshots.json --strict
	PYTHONDONTWRITEBYTECODE=1 python3 skills/design-craft/scripts/design_craft_l4_evidence_manifest.py --validate-screenshots-json evals/visual-reference/comparative-validation/reference-assisted-evidence-dossier/screenshots.json --strict

maturity-development:
	python3 scripts/design_craft_maturity.py --profile development

maturity-operational:
	@test -n "$(BENCHMARK_BASELINE)" || { echo "Set BENCHMARK_BASELINE to a committed benchmark baseline" >&2; exit 2; }
	python3 scripts/design_craft_maturity.py --profile operational_95 --baseline "$(BENCHMARK_BASELINE)"

maturity-certified:
	@test -n "$(BENCHMARK_BASELINE)" || { echo "Set BENCHMARK_BASELINE to a committed benchmark baseline" >&2; exit 2; }
	python3 scripts/design_craft_maturity.py --profile certified_100 --baseline "$(BENCHMARK_BASELINE)"

pass:
	bash skills/design-craft/scripts/design_craft_pass.sh --target . --mode audit --skip-route

audit:
	bash skills/design-craft/scripts/design_craft_audit.sh --target . --mode audit --skip-route

critique:
	bash skills/design-craft/scripts/design_craft_audit.sh --target . --mode critique --skip-route

prototype:
	python3 -m unittest tests.unit.test_prototype_contract
	bash skills/design-craft/scripts/design_craft_pass.sh --target skills/design-craft --mode prototype --skip-route --skip-detector --skip-score

system-review:
	python3 -m unittest tests.unit.test_system_review_contract
	bash skills/design-craft/scripts/design_craft_pass.sh --target skills/design-craft --mode system-review --skip-route --skip-detector --skip-score

primitive-selection:
	python3 -m unittest tests.unit.test_component_primitive_contract

motion:
	bash skills/design-craft/scripts/design_craft_pass.sh --target skills/design-craft --mode motion --skip-route --skip-score

motion-plan-dry-run:
	@tmp_dir="$$(mktemp -d -t design-craft-motion-plan.XXXXXX)" && trap 'rm -rf "$$tmp_dir"' EXIT && python3 skills/design-craft/scripts/design_craft_motion_plan.py --target "$$tmp_dir" --title "Retarget the sheet from its presentation value" --severity P1 --category interruptibility --dry-run >/dev/null

taste-review:
	bash skills/design-craft/scripts/design_craft_taste_review.sh --target skills/design-craft --context "release smoke" --evidence-level L0 >/dev/null

seed-dry-run:
	@tmp_dir="$$(mktemp -d -t design-craft-seed-dry-run.XXXXXX)" && trap 'rm -rf "$$tmp_dir"' EXIT && bash skills/design-craft/scripts/design_craft_seed_design.sh --target "$$tmp_dir" --dry-run

route-smoke:
	@tmp_dir="$$(mktemp -d -t design-craft-route-smoke.XXXXXX)"; \
	trap 'rm -rf "$$tmp_dir"' EXIT; \
	{ \
	  printf '%s\n' '# Project Design Authority'; \
	  printf '%s\n' ''; \
	  printf '%s\n' '## Typography System'; \
	  printf '%s\n' 'Readable typography contract.'; \
	  printf '%s\n' ''; \
	  printf '%s\n' '## Color Palette'; \
	  printf '%s\n' 'Token-backed color system.'; \
	  printf '%s\n' ''; \
	  printf '%s\n' '## Motion Language'; \
	  printf '%s\n' 'Calm interaction language.'; \
	  printf '%s\n' ''; \
	  printf '%s\n' '## Component Grammar'; \
	  printf '%s\n' 'Reusable component rules.'; \
	} > "$$tmp_dir/DESIGN.md"; \
		FRONTEND_ROUTE_TELEMETRY_LOG_ENABLED=0 FRONTEND_RUNTIME_SESSION_DISCOVERY=0 \
			  bash skills/design-craft/scripts/design_craft_route.sh --target "$$tmp_dir" --surface dashboard --intent visual-refine --scope page >/dev/null

doctor:
	bash scripts/design_craft_doctor.sh --target . --json >/dev/null

platform-scan-check:
	@set -e; for platform in ios android adaptive; do python3 skills/design-craft/scripts/design_craft_platform_scan.py --target "evals/fixtures/platforms/$$platform/valid" --json --strict >/dev/null; if python3 skills/design-craft/scripts/design_craft_platform_scan.py --target "evals/fixtures/platforms/$$platform/invalid" --json --strict >/dev/null 2>&1; then echo "$$platform invalid platform fixture unexpectedly passed" >&2; exit 1; fi; done

native-runtime-probe:
	python3 scripts/design_craft_native_runtime_validate.py --write-probe evals/native-runtime/environment-probe.json --json

native-runtime-check:
	python3 scripts/design_craft_native_runtime_validate.py --validate --require ios --require android --require-real-device --require-current-source --json

native-release-bundle-check:
	python3 -m unittest tests.unit.test_native_archive tests.unit.test_native_bundle tests.unit.test_github_runs

native-release-bundle-build:
	@test -n "$(NATIVE_RUN_OBSERVATION)" || { echo "Set NATIVE_RUN_OBSERVATION to the verified native run observation JSON" >&2; exit 2; }
	@test -n "$(PHYSICAL_RUN_OBSERVATION)" || { echo "Set PHYSICAL_RUN_OBSERVATION to the verified physical-device run observation JSON" >&2; exit 2; }
	@test -n "$(NATIVE_IOS_SOURCE)" || { echo "Set NATIVE_IOS_SOURCE to the downloaded iOS evidence root" >&2; exit 2; }
	@test -n "$(NATIVE_ANDROID_SOURCE)" || { echo "Set NATIVE_ANDROID_SOURCE to the downloaded Android evidence root" >&2; exit 2; }
	@test -n "$(NATIVE_REAL_DEVICE_ROOT)" || { echo "Set NATIVE_REAL_DEVICE_ROOT to the physical-device evidence root" >&2; exit 2; }
	python3 -m tools.design_craft release native-bundle build --force --native-observation "$(NATIVE_RUN_OBSERVATION)" --physical-observation "$(PHYSICAL_RUN_OBSERVATION)" --ios-source "$(NATIVE_IOS_SOURCE)" --android-source "$(NATIVE_ANDROID_SOURCE)" --physical-device-source "$(NATIVE_REAL_DEVICE_ROOT)" --output-dir "$(RELEASE_ASSET_DIR)"

native-release-bundle-verify:
	python3 -m tools.design_craft release native-bundle validate --verify-run --output-dir "$(RELEASE_ASSET_DIR)"

codex-route-pack-check:
	python3 scripts/design_craft_codex_route_pack.py --check

codex-route-pack-host-check:
	python3 scripts/design_craft_codex_route_pack.py --strict

init-dry-run:
	@tmp_dir="$$(mktemp -d -t design-craft-init.XXXXXX)"; \
	trap 'rm -rf "$$tmp_dir"' EXIT; \
	bash scripts/design_craft_init_agent.sh --agent codex --target "$$tmp_dir" --scope project --dry-run >/dev/null; \
	bash scripts/design_craft_init_agent.sh --agent cursor --target "$$tmp_dir" --scope project --with-rule --dry-run >/dev/null; \
	bash scripts/design_craft_init_agent.sh --agent claude --target "$$tmp_dir" --scope project --dry-run >/dev/null; \
	bash scripts/design_craft_init_agent.sh --agent pi --target "$$tmp_dir" --scope project --dry-run >/dev/null; \
	bash scripts/design_craft_init_agent.sh --agent generic --target "$$tmp_dir" --scope project --dry-run >/dev/null

active-scope-check:
	python3 scripts/design_craft_active_scope_validate.py --root . >/dev/null

cross-agent-check:
	python3 scripts/design_craft_cross_agent_validate.py --root evals/cross-agent >/dev/null

cross-agent-history-check:
	python3 scripts/design_craft_cross_agent_validate.py --history-root evals/cross-agent/history >/dev/null

cross-agent-observed-check:
	python3 scripts/design_craft_cross_agent_validate.py --observed-task evals/cross-agent/same-prompt-dashboard-review >/dev/null
	python3 scripts/design_craft_cross_agent_validate.py --observed-task evals/cross-agent/same-prompt-motion-review >/dev/null
	python3 scripts/design_craft_cross_agent_validate.py --observed-task evals/cross-agent/same-prompt-native-adaptive-review >/dev/null

cross-agent-four-host-check:
	@set -e; for task in same-prompt-dashboard-review same-prompt-motion-review same-prompt-native-adaptive-review; do python3 scripts/design_craft_cross_agent_validate.py --observed-task "evals/cross-agent/$$task" --require-host codex --require-host pi --require-host cursor --require-host claude; done

cross-agent-motion-observed-check:
	python3 scripts/design_craft_cross_agent_validate.py --observed-task evals/cross-agent/same-prompt-motion-review >/dev/null

cross-agent-native-observed-check:
	python3 scripts/design_craft_cross_agent_validate.py --observed-task evals/cross-agent/same-prompt-native-adaptive-review >/dev/null

comparative-check:
	python3 scripts/design_craft_comparative_run.py --check
	python3 scripts/design_craft_comparative_judge.py --check
	python3 scripts/design_craft_comparative_validate.py --check

comparative-history-check:
	python3 scripts/design_craft_comparative_validate.py --history-root evals/comparative/history

history-audit: cross-agent-history-check comparative-history-check

comparative-observed-check:
	python3 scripts/design_craft_comparative_validate.py --require-observed

l4-capture-check:
	python3 skills/design-craft/scripts/design_craft_l4_capture.py --check >/dev/null

historical-l4-metadata-check:
	@case_dir="evals/product-ui-taste/before-after/data""hub-live""-center-review-workbench"; \
	python3 skills/design-craft/scripts/design_craft_l4_case_validate.py --case-dir "$$case_dir" --strict >/dev/null

real-l4-check:
	python3 skills/design-craft/scripts/design_craft_l4_case_validate.py --case-dir evals/product-ui-taste/before-after/generic-review-workbench-local-l4 --strict --require-existing-files >/dev/null

smell-smoke:
	python3 skills/design-craft/scripts/design_craft_css_smell_scan.py --target evals/fixtures/css-smells --json >/dev/null
	python3 skills/design-craft/scripts/design_craft_focus_audit.py --target evals/fixtures/focus-smells --json >/dev/null
	python3 skills/design-craft/scripts/design_craft_token_audit.py --target evals/fixtures/token-smells --json >/dev/null
	python3 skills/design-craft/scripts/design_craft_static_review.py --target evals/fixtures --json >/dev/null

static-review-smoke:
	python3 skills/design-craft/scripts/design_craft_static_review.py --target evals/fixtures --json >/dev/null

upstream-report:
	python3 scripts/upstream_absorption_report.py

taste-absorption-check:
	python3 scripts/design_craft_taste_absorption.py --check --strict

impeccable-absorption-check:
	python3 scripts/design_craft_impeccable_absorption.py --check --strict
	python3 -m unittest tests.unit.test_impeccable_detector_contract

emil-absorption-check:
	python3 scripts/design_craft_emil_absorption.py --check --strict

jakub-absorption-check:
	python3 -m unittest tests.unit.test_jakub_upstream_contract

upstream-absorption-check: taste-absorption-check impeccable-absorption-check emil-absorption-check jakub-absorption-check

upstream-freshness-audit:
	python3 scripts/upstream_absorption_report.py --remote-details --fail-on-unreviewed

upstream-remote-report: upstream-freshness-audit

sync-status:
	python3 scripts/design_craft_sync_status.py

sync-status-remote:
	python3 scripts/design_craft_sync_status.py --remote

sync-status-check:
	python3 scripts/design_craft_sync_status.py --check

install:
	bash scripts/install_local.sh $(INSTALL_ARGS)

install-verify:
	python3 scripts/design_craft_install_verify.py --source skills/design-craft --installed "$(DESIGN_CRAFT_SKILL_ROOT)/design-craft" --expected-name design-craft --expected-version "$$(cat VERSION)" --require-metadata

release-gate-source: validate-portable lint contract-tests package-check public-repo-check workflow-check skill-quick-validate score visual-reference-check maturity-development pass audit critique prototype system-review motion primitive-selection motion-plan-dry-run taste-review seed-dry-run route-smoke doctor platform-scan-check native-release-bundle-check codex-route-pack-check init-dry-run active-scope-check cross-agent-check comparative-check l4-capture-check historical-l4-metadata-check smell-smoke upstream-report upstream-absorption-check github-governance-contract-check

publish-local: release-gate-source
	bash scripts/install_local.sh $(INSTALL_ARGS)
	$(MAKE) install-verify
	$(MAKE) sync-status-check
	$(MAKE) maturity-development

github-governance-contract-check:
	python3 scripts/design_craft_github_governance.py --check

github-governance-check:
	python3 scripts/design_craft_github_governance.py

github-governance-apply:
	python3 scripts/design_craft_github_governance.py --apply --confirm-external-write

release-readiness-operational: publish-local
	@test -n "$(BENCHMARK_BASELINE)" || { echo "Set BENCHMARK_BASELINE to a committed benchmark baseline" >&2; exit 2; }
	python3 -m tools.design_craft release verify --level operational_95 --phase candidate --baseline "$(BENCHMARK_BASELINE)" $(if $(BENCHMARK_RESULT),--benchmark-result "$(BENCHMARK_RESULT)",) --output "$(OPERATIONAL_CANDIDATE_EVIDENCE)"

release-tag-verify-operational:
	@test -n "$(BENCHMARK_BASELINE)" || { echo "Set BENCHMARK_BASELINE to a committed benchmark baseline" >&2; exit 2; }
	@test -n "$(BENCHMARK_RESULT)" || { echo "Set BENCHMARK_RESULT to the selected full benchmark result" >&2; exit 2; }
	@test -n "$(BENCHMARK_RUN_OBSERVATION)" || { echo "Set BENCHMARK_RUN_OBSERVATION to the verified benchmark run observation JSON" >&2; exit 2; }
	python3 -m tools.design_craft release verify --level operational_95 --phase final --baseline "$(BENCHMARK_BASELINE)" --benchmark-result "$(BENCHMARK_RESULT)" --benchmark-observation "$(BENCHMARK_RUN_OBSERVATION)" --output "$(OPERATIONAL_FINAL_EVIDENCE)"
	python3 scripts/design_craft_github_checks.py --level operational_95 --require-tag-run

release-assets-build-operational:
	@test -n "$(NATIVE_RUN_OBSERVATION)" || { echo "Set NATIVE_RUN_OBSERVATION to the verified native run observation JSON" >&2; exit 2; }
	@test -n "$(BENCHMARK_RUN_OBSERVATION)" || { echo "Set BENCHMARK_RUN_OBSERVATION to the verified benchmark run observation JSON" >&2; exit 2; }
	@test -n "$(BENCHMARK_RESULT)" || { echo "Set BENCHMARK_RESULT to the selected full benchmark result" >&2; exit 2; }
	@test -n "$(NATIVE_EVIDENCE_ROOT)" || { echo "Set NATIVE_EVIDENCE_ROOT to the downloaded native evidence root" >&2; exit 2; }
	python3 -m tools.design_craft release evidence-bindings --level operational_95 --evidence "$(OPERATIONAL_FINAL_EVIDENCE)" --evidence-root "$(NATIVE_EVIDENCE_ROOT)" --native-observation "$(NATIVE_RUN_OBSERVATION)" --benchmark-observation "$(BENCHMARK_RUN_OBSERVATION)" --benchmark-result "$(BENCHMARK_RESULT)"
	python3 -m tools.design_craft release assets --level operational_95 --build --force --evidence "$(OPERATIONAL_FINAL_EVIDENCE)" --evidence-root "$(NATIVE_EVIDENCE_ROOT)" --output-dir "$(RELEASE_ASSET_DIR)"

release-assets-verify-operational:
	python3 -m tools.design_craft release assets --level operational_95 --output-dir "$(RELEASE_ASSET_DIR)"

release-final-verify-operational: release-tag-verify-operational release-assets-verify-operational
	python3 scripts/design_craft_github_checks.py --level operational_95 --require-tag-run --require-release-assets

release-readiness-certified: publish-local
	@test -n "$(BENCHMARK_BASELINE)" || { echo "Set BENCHMARK_BASELINE to a committed benchmark baseline" >&2; exit 2; }
	python3 -m tools.design_craft release verify --level certified_100 --phase candidate --baseline "$(BENCHMARK_BASELINE)" $(if $(BENCHMARK_RESULT),--benchmark-result "$(BENCHMARK_RESULT)",) --output "$(CERTIFIED_CANDIDATE_EVIDENCE)"

release-tag-verify-certified:
	@test -n "$(BENCHMARK_BASELINE)" || { echo "Set BENCHMARK_BASELINE to a committed benchmark baseline" >&2; exit 2; }
	@test -n "$(BENCHMARK_RESULT)" || { echo "Set BENCHMARK_RESULT to the selected full benchmark result" >&2; exit 2; }
	@test -n "$(BENCHMARK_RUN_OBSERVATION)" || { echo "Set BENCHMARK_RUN_OBSERVATION to the verified benchmark run observation JSON" >&2; exit 2; }
	python3 -m tools.design_craft release verify --level certified_100 --phase final --baseline "$(BENCHMARK_BASELINE)" --benchmark-result "$(BENCHMARK_RESULT)" --benchmark-observation "$(BENCHMARK_RUN_OBSERVATION)" --output "$(CERTIFIED_FINAL_EVIDENCE)"
	python3 scripts/design_craft_github_checks.py --level certified_100 --require-tag-run

release-assets-build-certified:
	@test -n "$(NATIVE_RUN_OBSERVATION)" || { echo "Set NATIVE_RUN_OBSERVATION to the verified native run observation JSON" >&2; exit 2; }
	@test -n "$(PHYSICAL_RUN_OBSERVATION)" || { echo "Set PHYSICAL_RUN_OBSERVATION to the verified physical-device run observation JSON" >&2; exit 2; }
	@test -n "$(BENCHMARK_RUN_OBSERVATION)" || { echo "Set BENCHMARK_RUN_OBSERVATION to the verified benchmark run observation JSON" >&2; exit 2; }
	@test -n "$(BENCHMARK_RESULT)" || { echo "Set BENCHMARK_RESULT to the selected full benchmark result" >&2; exit 2; }
	@test -n "$(NATIVE_EVIDENCE_ROOT)" || { echo "Set NATIVE_EVIDENCE_ROOT to the downloaded native evidence root" >&2; exit 2; }
	python3 -m tools.design_craft release evidence-bindings --level certified_100 --evidence "$(CERTIFIED_FINAL_EVIDENCE)" --evidence-root "$(NATIVE_EVIDENCE_ROOT)" --native-observation "$(NATIVE_RUN_OBSERVATION)" --benchmark-observation "$(BENCHMARK_RUN_OBSERVATION)" --benchmark-result "$(BENCHMARK_RESULT)" --physical-observation "$(PHYSICAL_RUN_OBSERVATION)"
	$(MAKE) native-release-bundle-build
	python3 -m tools.design_craft release assets --level certified_100 --build --force --evidence "$(CERTIFIED_FINAL_EVIDENCE)" --evidence-root "$(NATIVE_EVIDENCE_ROOT)" --output-dir "$(RELEASE_ASSET_DIR)"

release-assets-verify-certified:
	python3 -m tools.design_craft release assets --level certified_100 --output-dir "$(RELEASE_ASSET_DIR)"
	python3 -m tools.design_craft release native-bundle validate --verify-run --output-dir "$(RELEASE_ASSET_DIR)"

release-final-verify-certified: release-tag-verify-certified release-assets-verify-certified
	python3 scripts/design_craft_github_checks.py --level certified_100 --require-tag-run --require-release-assets

release-certification-build-operational:
	@test -n "$(NATIVE_EVIDENCE_ROOT)" || { echo "Set NATIVE_EVIDENCE_ROOT to the downloaded native evidence root" >&2; exit 2; }
	@test -n "$(NATIVE_RUN_OBSERVATION)" || { echo "Set NATIVE_RUN_OBSERVATION to the verified native run observation JSON" >&2; exit 2; }
	@test -n "$(BENCHMARK_RUN_OBSERVATION)" || { echo "Set BENCHMARK_RUN_OBSERVATION to the verified benchmark run observation JSON" >&2; exit 2; }
	@test -n "$(BENCHMARK_RESULT)" || { echo "Set BENCHMARK_RESULT to the selected full benchmark result" >&2; exit 2; }
	@test -n "$(CERTIFICATION_REPOSITORY)" || { echo "Set CERTIFICATION_REPOSITORY to owner/name" >&2; exit 2; }
	@test -n "$(CERTIFICATION_RUN_ID)" || { echo "Set CERTIFICATION_RUN_ID to the certification workflow run ID" >&2; exit 2; }
	@test -n "$(CERTIFICATION_RUN_ATTEMPT)" || { echo "Set CERTIFICATION_RUN_ATTEMPT to the certification workflow run attempt" >&2; exit 2; }
	python3 -m tools.design_craft release certification build --level operational_95 --tag "$(CERTIFICATION_TAG)" --evidence "$(OPERATIONAL_FINAL_EVIDENCE)" --evidence-root "$(NATIVE_EVIDENCE_ROOT)" --native-observation "$(NATIVE_RUN_OBSERVATION)" --benchmark-observation "$(BENCHMARK_RUN_OBSERVATION)" --benchmark-result "$(BENCHMARK_RESULT)" --assets-dir "$(RELEASE_ASSET_DIR)" --repository "$(CERTIFICATION_REPOSITORY)" --workflow-run-id "$(CERTIFICATION_RUN_ID)" --workflow-run-attempt "$(CERTIFICATION_RUN_ATTEMPT)" --output-dir "$(CERTIFICATION_BUNDLE_DIR)"

release-certification-verify-operational:
	python3 -m tools.design_craft release certification validate --level operational_95 --input-dir "$(CERTIFICATION_BUNDLE_DIR)"

release-certification-build-certified:
	@test -n "$(NATIVE_EVIDENCE_ROOT)" || { echo "Set NATIVE_EVIDENCE_ROOT to the downloaded native evidence root" >&2; exit 2; }
	@test -n "$(NATIVE_RUN_OBSERVATION)" || { echo "Set NATIVE_RUN_OBSERVATION to the verified native run observation JSON" >&2; exit 2; }
	@test -n "$(PHYSICAL_RUN_OBSERVATION)" || { echo "Set PHYSICAL_RUN_OBSERVATION to the verified physical-device run observation JSON" >&2; exit 2; }
	@test -n "$(BENCHMARK_RUN_OBSERVATION)" || { echo "Set BENCHMARK_RUN_OBSERVATION to the verified benchmark run observation JSON" >&2; exit 2; }
	@test -n "$(BENCHMARK_RESULT)" || { echo "Set BENCHMARK_RESULT to the selected full benchmark result" >&2; exit 2; }
	@test -n "$(CERTIFICATION_REPOSITORY)" || { echo "Set CERTIFICATION_REPOSITORY to owner/name" >&2; exit 2; }
	@test -n "$(CERTIFICATION_RUN_ID)" || { echo "Set CERTIFICATION_RUN_ID to the certification workflow run ID" >&2; exit 2; }
	@test -n "$(CERTIFICATION_RUN_ATTEMPT)" || { echo "Set CERTIFICATION_RUN_ATTEMPT to the certification workflow run attempt" >&2; exit 2; }
	python3 -m tools.design_craft release certification build --level certified_100 --tag "$(CERTIFICATION_TAG)" --evidence "$(CERTIFIED_FINAL_EVIDENCE)" --evidence-root "$(NATIVE_EVIDENCE_ROOT)" --native-observation "$(NATIVE_RUN_OBSERVATION)" --benchmark-observation "$(BENCHMARK_RUN_OBSERVATION)" --benchmark-result "$(BENCHMARK_RESULT)" --physical-observation "$(PHYSICAL_RUN_OBSERVATION)" --assets-dir "$(RELEASE_ASSET_DIR)" --repository "$(CERTIFICATION_REPOSITORY)" --workflow-run-id "$(CERTIFICATION_RUN_ID)" --workflow-run-attempt "$(CERTIFICATION_RUN_ATTEMPT)" --output-dir "$(CERTIFICATION_BUNDLE_DIR)"

release-certification-verify-certified:
	python3 -m tools.design_craft release certification validate --level certified_100 --input-dir "$(CERTIFICATION_BUNDLE_DIR)"
