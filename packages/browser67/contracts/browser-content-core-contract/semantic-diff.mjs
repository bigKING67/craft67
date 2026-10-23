import assert from "node:assert/strict";

import { semanticDiffSnapshots } from "../../src/browser/content/semantic-diff.mjs";

function node(id, name, locators = [], frame = []) {
  return {
    node_id: id,
    tag: "button",
    role: "button",
    accessible_name: name,
    text: id,
    frame_path: frame,
    locator_candidates: locators.map(([type, value]) => ({ type, value })),
  };
}

function diff(before, after) {
  return semanticDiffSnapshots(
    { snapshot_id: "before", document_id: "doc", nodes: before },
    { snapshot_id: "after", document_id: "doc", nodes: after },
  );
}

function pairs(result) {
  return result.changed_nodes.map((item) => [item.before_node_id, item.node_id, item.confidence]);
}

function assertSemanticDiffMatching() {
  const precedence = diff(
    [node("before", "same", [["marker", "later"], ["id", "first"]])],
    [node("first", "same", [["id", "first"]]), node("later", "same", [["marker", "later"]])],
  );
  assert.deepEqual(pairs(precedence), [["before", "first", "high"]]);
  assert.deepEqual(precedence.added_nodes.map((item) => item.node_id), ["later"]);

  const ambiguity = diff(
    [node("ambiguous", "same"), node("stable", "same", [["id", "first"]]), node("unique", "same")],
    [node("first", "same", [["id", "first"]]), node("second", "same")],
  );
  assert.deepEqual(pairs(ambiguity), [["stable", "first", "high"], ["unique", "second", "medium"]]);
  assert.deepEqual(ambiguity.removed_nodes.map((item) => item.node_id), ["ambiguous"]);

  const exhausted = diff(
    [node("stable", "other", [["id", "shared"]]), node("fallback", "same", [["id", "shared"]])],
    [node("first", "other", [["id", "shared"]]), node("second", "same")],
  );
  assert.deepEqual(pairs(exhausted), [["stable", "first", "high"], ["fallback", "second", "medium"]]);

  const duplicates = diff(
    [node("a", "same", [["id", "duplicate"]]), node("b", "same", [["id", "duplicate"]])],
    [node("first", "same", [["id", "duplicate"], ["id", "duplicate"]]), node("second", "same", [["id", "duplicate"]])],
  );
  assert.deepEqual(pairs(duplicates), [["a", "first", "high"], ["b", "second", "high"]]);
  assert.equal(duplicates.summary.added_count, 0);

  const frames = diff(
    [node("inner", "same", [], ["frame"]), node("outer", "same")],
    [node("outer-after", "same"), node("inner-after", "same", [], ["frame"])],
  );
  assert.deepEqual(pairs(frames), [["inner", "inner-after", "medium"], ["outer", "outer-after", "medium"]]);
  assert.equal(frames.summary.removed_count, 0);
}

export { assertSemanticDiffMatching };
