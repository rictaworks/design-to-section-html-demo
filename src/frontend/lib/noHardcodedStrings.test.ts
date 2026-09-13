import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";

const ROOTS = ["app", "components"];
const ALLOWLIST = new Set([path.join("lib", "messages.ts")]);
const JAPANESE_RE = /[぀-ゟ゠-ヿ一-鿿]/;

function stripComments(source: string): string {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|[^:])\/\/.*$/gm, "$1");
}

function collectFiles(dir: string, acc: string[]) {
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      collectFiles(full, acc);
    } else if (/\.(ts|tsx)$/.test(entry) && !/\.test\.(ts|tsx)$/.test(entry)) {
      acc.push(full);
    }
  }
}

describe("no hardcoded Japanese UI strings outside lib/messages.ts", () => {
  it("finds no Japanese string literals in app/ or components/ source files", () => {
    const root = path.resolve(__dirname, "..");
    const files: string[] = [];
    for (const dir of ROOTS) {
      collectFiles(path.join(root, dir), files);
    }

    const offenders = files
      .map((file) => path.relative(root, file))
      .filter((rel) => !ALLOWLIST.has(rel))
      .filter((rel) => {
        const source = stripComments(readFileSync(path.join(root, rel), "utf-8"));
        return JAPANESE_RE.test(source);
      });

    expect(offenders).toEqual([]);
  });
});
