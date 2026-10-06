/**
 * Terminating structured-output tools used only by the development evaluator.
 *
 * Pi validates tool arguments against these schemas before execution. The
 * Python evaluator still applies its stricter case-specific contracts after it
 * extracts the tool call, so schema-valid output is not automatically a pass.
 */

import { StringEnum } from "@earendil-works/pi-ai";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

const Status = StringEnum(["PASS", "FAIL", "UNCERTAIN"] as const);
const MustStatus = StringEnum(["PASS", "FAIL", "UNCERTAIN"] as const, {
	description:
		"PASS when the candidate satisfies this required criterion; FAIL when it does not; UNCERTAIN only when the evidence is insufficient.",
});
const ProhibitedBehaviorPresence = StringEnum(
	["ABSENT", "PRESENT", "UNCERTAIN"] as const,
	{
	description:
			"Whether the prohibited behavior appears in the candidate: ABSENT when it does not appear, PRESENT when it appears, or UNCERTAIN only when presence cannot be determined.",
	},
);
const NonEmptyString = Type.String({ minLength: 1 });

const MustCheck = Type.Object(
	{
		criterion_index: Type.Integer({ minimum: 1 }),
		status: MustStatus,
		evidence: NonEmptyString,
	},
	{ additionalProperties: false },
);

const MustNotCheck = Type.Object(
	{
		criterion_index: Type.Integer({ minimum: 1 }),
		presence: ProhibitedBehaviorPresence,
		evidence: NonEmptyString,
	},
	{ additionalProperties: false },
);

const ReaderAnswer = Type.Object(
	{
		question_id: NonEmptyString,
		answer: NonEmptyString,
		evidence: NonEmptyString,
	},
	{ additionalProperties: false },
);

const ReaderCheck = Type.Object(
	{
		question_id: NonEmptyString,
		status: Status,
		evidence: NonEmptyString,
	},
	{ additionalProperties: false },
);

const submitFactJudgment = defineTool({
	name: "submit_fact_judgment",
	label: "Submit fact judgment",
	description: "Submit the final fact and contract judgment for one Write Craft evaluation case.",
	promptSnippet: "Submit the final fact judgment through submit_fact_judgment",
	promptGuidelines: [
		"Use submit_fact_judgment exactly once as the final action when judging a Write Craft candidate.",
		"Identify each contract criterion by its 1-based criterion_index in the original order; do not copy or rewrite criterion text.",
		"For must_not items, set presence to ABSENT when the prohibited behavior does not appear and PRESENT when it appears.",
		"Do not supply an overall status; the evaluator computes it from the individual checks and blocking issues.",
		"Do not emit a JSON or prose answer instead of the tool call.",
	],
	parameters: Type.Object(
		{
			schema: StringEnum(["write-craft.judgment.v1"] as const),
			case_id: NonEmptyString,
			must: Type.Array(MustCheck, {
				description: "Required criteria in original order, identified by 1-based criterion_index.",
			}),
			must_not: Type.Array(MustNotCheck, {
				description: "Prohibited behaviors in original order, identified by 1-based criterion_index and classified by presence.",
			}),
			blocking_issues: Type.Array(NonEmptyString),
			editorial: Type.Object({
				schema: StringEnum(["write-craft.editorial.v1"] as const),
				issues: Type.Array(Type.Object({
					kind: StringEnum(["redundancy", "irrelevant_commentary", "structure", "sentence", "wording", "presentation"] as const),
					quote: NonEmptyString,
					reason: NonEmptyString,
					suggestion: NonEmptyString,
				}, { additionalProperties: false })),
			}, { additionalProperties: false }),
		},
		{ additionalProperties: false },
	),
	async execute() {
		return {
			content: [{ type: "text" as const, text: "Fact judgment submitted." }],
			terminate: true,
		};
	},
});

const submitReaderResponse = defineTool({
	name: "submit_reader_response",
	label: "Submit reader response",
	description: "Submit the final blind-reader response for one Write Craft evaluation case.",
	promptSnippet: "Submit the final blind-reader response through submit_reader_response",
	promptGuidelines: [
		"Use submit_reader_response exactly once as the final action for a Write Craft blind-reader task.",
		"Do not emit a JSON or prose answer instead of the tool call.",
	],
	parameters: Type.Object(
		{
			schema: StringEnum(["write-craft.reader-response.v1"] as const),
			case_id: NonEmptyString,
			restatement: NonEmptyString,
			answers: Type.Array(ReaderAnswer),
			ambiguities: Type.Array(NonEmptyString),
			natural_questions: Type.Array(NonEmptyString),
		},
		{ additionalProperties: false },
	),
	async execute() {
		return {
			content: [{ type: "text" as const, text: "Reader response submitted." }],
			terminate: true,
		};
	},
});

const submitReaderJudgment = defineTool({
	name: "submit_reader_judgment",
	label: "Submit reader judgment",
	description: "Submit the final reader-understanding judgment for one Write Craft evaluation case.",
	promptSnippet: "Submit the final reader judgment through submit_reader_judgment",
	promptGuidelines: [
		"Use submit_reader_judgment exactly once as the final action when checking Write Craft reader understanding.",
		"Do not emit a JSON or prose answer instead of the tool call.",
	],
	parameters: Type.Object(
		{
			schema: StringEnum(["write-craft.reader-judgment.v1"] as const),
			case_id: NonEmptyString,
			status: Status,
			answers: Type.Array(ReaderCheck),
			blocking_issues: Type.Array(NonEmptyString),
		},
		{ additionalProperties: false },
	),
	async execute() {
		return {
			content: [{ type: "text" as const, text: "Reader judgment submitted." }],
			terminate: true,
		};
	},
});

export default function registerEvalStructuredOutput(pi: ExtensionAPI) {
	pi.registerTool(submitFactJudgment);
	pi.registerTool(submitReaderResponse);
	pi.registerTool(submitReaderJudgment);
}
