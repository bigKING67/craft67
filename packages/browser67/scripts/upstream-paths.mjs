import { existsSync } from "node:fs";
import { resolve } from "node:path";

/** GenericAgent remains a sibling of the source checkout, outside craft67. */
export function defaultGenericAgentRoot(packageRoot) {
  const monorepoRoot = resolve(packageRoot, "../..");
  const inCraft67 = existsSync(resolve(monorepoRoot, "catalog.json"))
    && resolve(monorepoRoot, "packages/browser67") === resolve(packageRoot);
  return resolve(inCraft67 ? monorepoRoot : packageRoot, "../GenericAgent");
}
