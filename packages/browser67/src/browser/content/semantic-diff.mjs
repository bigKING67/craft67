import { createToolError } from "../../runtime/tool-errors.mjs";
import { browserSnapshotStore } from "./snapshot-store.mjs";

const DIFF_FIELDS = [
  "text",
  "value",
  "visible",
  "enabled",
  "checked",
  "selected",
  "rect",
  "role",
  "accessible_name",
];

function equalValue(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
}

function identityCandidates(node) {
  return (node.locator_candidates ?? [])
    .filter((item) => ["marker", "id", "testid", "name"].includes(item.type))
    .map((item) => `${item.type}:${item.value}`);
}

function semanticIdentity(node) {
  return `${(node.frame_path ?? []).join("/")}|${node.tag}|${node.role}|${node.accessible_name}`;
}

function matchNodes(beforeNodes, afterNodes) {
  const unmatchedAfter = new Set(afterNodes.map((_item, index) => index));
  const stableIdentities = afterNodes.map(identityCandidates);
  const semanticIdentities = afterNodes.map(semanticIdentity);
  const stableIndex = new Map();
  const semanticIndex = new Map();
  function addCandidate(index, key, candidateIndex) {
    if (!index.has(key)) index.set(key, new Set());
    index.get(key).add(candidateIndex);
  }
  for (const [index, identities] of stableIdentities.entries()) {
    for (const identity of identities) addCandidate(stableIndex, identity, index);
    addCandidate(semanticIndex, semanticIdentities[index], index);
  }
  const matches = [];
  for (const before of beforeNodes) {
    let index = -1;
    let confidence = "low";
    const stable = new Set(identityCandidates(before));
    for (const identity of stable) {
      const candidate = stableIndex.get(identity)?.values().next().value;
      if (candidate !== undefined && (index < 0 || candidate < index)) index = candidate;
    }
    if (index >= 0) confidence = "high";
    if (index < 0) {
      const candidates = semanticIndex.get(semanticIdentity(before));
      if (candidates?.size === 1) {
        index = candidates.values().next().value;
        confidence = "medium";
      }
    }
    if (index >= 0) {
      unmatchedAfter.delete(index);
      for (const identity of stableIdentities[index]) stableIndex.get(identity).delete(index);
      semanticIndex.get(semanticIdentities[index]).delete(index);
      matches.push({ before, after: afterNodes[index], confidence });
    } else {
      matches.push({ before, after: null, confidence: "none" });
    }
  }
  return { matches, unmatchedAfter };
}

function semanticDiffSnapshots(before, after) {
  if (!before || !after) {
    throw createToolError("INVALID_ARGUMENT", "semantic diff requires two snapshots", { retryable: false });
  }
  const { matches, unmatchedAfter } = matchNodes(before.nodes ?? [], after.nodes ?? []);
  const removedNodes = matches
    .filter((match) => !match.after)
    .map((match) => match.before);
  const addedNodes = [...unmatchedAfter].map((index) => after.nodes[index]);
  const changedNodes = [];
  for (const match of matches) {
    if (!match.after) continue;
    const changes = {};
    for (const field of DIFF_FIELDS) {
      if (!equalValue(match.before[field], match.after[field])) {
        changes[field] = { before: match.before[field], after: match.after[field] };
      }
    }
    if (Object.keys(changes).length > 0) {
      changedNodes.push({
        node_id: match.after.node_id,
        before_node_id: match.before.node_id,
        confidence: match.confidence,
        changes,
      });
    }
  }
  const transientChanges = {
    before: before.transients ?? [],
    after: after.transients ?? [],
    changed: !equalValue(before.transients ?? [], after.transients ?? []),
  };
  const documentChanged = before.document_id !== after.document_id;
  return {
    schema: "browser67.semantic-diff.v2",
    before_snapshot_id: before.snapshot_id,
    after_snapshot_id: after.snapshot_id,
    page_state_changed: documentChanged || addedNodes.length > 0 || removedNodes.length > 0 || changedNodes.length > 0 || transientChanges.changed,
    document_changed: documentChanged,
    added_nodes: addedNodes,
    removed_nodes: removedNodes,
    changed_nodes: changedNodes,
    transient_changes: transientChanges,
    summary: {
      added_count: addedNodes.length,
      removed_count: removedNodes.length,
      changed_count: changedNodes.length,
      before_node_count: before.nodes?.length ?? 0,
      after_node_count: after.nodes?.length ?? 0,
    },
  };
}

function diffStoredSnapshots(args = {}, store = browserSnapshotStore) {
  const before = store.get(args.before_snapshot_id, args, { require_scope: true });
  const after = store.get(args.after_snapshot_id, args, { require_scope: true });
  if (before.workspace_key !== after.workspace_key || before.task_id !== after.task_id) {
    throw createToolError("SNAPSHOT_SCOPE_MISMATCH", "snapshots belong to different workspace/task scopes", {
      retryable: false,
    });
  }
  return semanticDiffSnapshots(before, after);
}

export { diffStoredSnapshots, semanticDiffSnapshots };
