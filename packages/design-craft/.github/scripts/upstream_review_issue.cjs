const fs = require("fs/promises");

const TITLE = "[design-craft] Upstream review required";

module.exports = async function maintainUpstreamReviewIssue({
  github,
  context,
  mode,
  reportPath = "upstream-audit.txt",
}) {
  const { data: issues } = await github.rest.issues.listForRepo({
    owner: context.repo.owner,
    repo: context.repo.repo,
    state: "open",
    per_page: 100,
  });
  const existing = issues.find((issue) => issue.title === TITLE && !issue.pull_request);

  if (mode === "resolved") {
    if (!existing) return;
    await github.rest.issues.createComment({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: existing.number,
      body: `Resolved by upstream audit run ${process.env.GITHUB_RUN_ID}.`,
    });
    await github.rest.issues.update({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: existing.number,
      state: "closed",
    });
    return;
  }

  if (mode !== "drift") {
    throw new Error(`Unsupported upstream review issue mode: ${mode}`);
  }
  const report = (await fs.readFile(reportPath, "utf8")).slice(0, 50000);
  const body = [
    "The daily upstream freshness audit found unreviewed remote drift.",
    "",
    `Workflow: ${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}`,
    "",
    "```text",
    report,
    "```",
  ].join("\n");

  if (existing) {
    await github.rest.issues.update({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: existing.number,
      body,
    });
    return;
  }
  await github.rest.issues.create({
    owner: context.repo.owner,
    repo: context.repo.repo,
    title: TITLE,
    body,
  });
};
