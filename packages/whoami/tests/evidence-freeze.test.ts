import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { contextFor } from "../src/evidence.js";

// 已发布的 evidence 版本冻结：v1 为历史样例口径，v2 随 2026-09-28 合并发布。
// 这些 evidenceId 取自发布时的输出；任何改动若使其变化，说明破坏了旧报告与验收的可重算性。
const example = JSON.parse(readFileSync("examples/birth.json", "utf8"));
const boundary = JSON.parse(readFileSync("examples/acceptance/boundary/birth.json", "utf8"));

const FROZEN = [
  { input: example, years: [2026], schema: "whoami.evidence.v1", granularity: "year", id: "821d437569b9eaf0d0cdddd3fbd029f9c9bdb441d93dbf6f87082cce7f3f74eb" },
  { input: example, years: [2026], schema: "whoami.evidence.v2", granularity: "year", id: "41906430ea0e0d77b133f6d50166d0676b5cb93af2a0caa5b5b2cf59d6675a18" },
  { input: example, years: [2025], schema: "whoami.evidence.v2", granularity: "month", id: "e0173ace68b52c459e9e92a473876b444b2335d7e9dd696ce9b2d7dd23a6da09" },
  { input: boundary, years: [2026, 2027, 2028], schema: "whoami.evidence.v1", granularity: "year", id: "fc3486c375cc98e4f15087813ba851a03b1af3b26625790f3fa01f6d517acd3f" },
  { input: boundary, years: [2026, 2027, 2028], schema: "whoami.evidence.v2", granularity: "year", id: "62a5b05981632d94e34a7e8570ac4040ada41b41c5b1eb8b587b4c720ae1d016" },
] as const;

test("已发布的 evidence v1/v2 输出保持冻结", () => {
  for (const f of FROZEN)
    assert.equal(
      contextFor(f.input, [...f.years], f.schema, f.granularity).evidenceId,
      f.id,
      `${f.schema} ${f.granularity} ${f.years.join(",")}`,
    );
});
