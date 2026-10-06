"use strict";

const assert = require("assert");
const maintainIssue = require("../../.github/scripts/upstream_review_issue.cjs");

function mockGithub(issues) {
  const calls = [];
  return {
    calls,
    rest: {
      issues: {
        listForRepo: async () => ({ data: issues }),
        create: async (args) => calls.push(["create", args]),
        update: async (args) => calls.push(["update", args]),
        createComment: async (args) => calls.push(["comment", args]),
      },
    },
  };
}

async function main() {
  process.env.GITHUB_SERVER_URL = "https://github.com";
  process.env.GITHUB_REPOSITORY = "example/design-craft";
  process.env.GITHUB_RUN_ID = "1";
  const context = { repo: { owner: "example", repo: "design-craft" } };

  const created = mockGithub([]);
  await maintainIssue({ github: created, context, mode: "drift", reportPath: "README.md" });
  assert.equal(created.calls[0][0], "create");

  const issue = { number: 7, title: "[design-craft] Upstream review required" };
  const updated = mockGithub([issue]);
  await maintainIssue({ github: updated, context, mode: "drift", reportPath: "README.md" });
  assert.equal(updated.calls[0][0], "update");

  const resolved = mockGithub([issue]);
  await maintainIssue({ github: resolved, context, mode: "resolved" });
  assert.deepEqual(
    resolved.calls.map((call) => call[0]),
    ["comment", "update"],
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
