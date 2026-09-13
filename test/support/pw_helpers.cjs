"use strict";
/**
 * Playwright(Node.js, playwright coreパッケージ)を使った簡易チェックランナー。
 * @playwright/test（テストランナー）はこの開発環境に無いため、
 * `playwright` コア（chromium.launch()等）を直接使う軽量な自作ランナー。
 *
 * DOCS/TM.md の方針どおり「実ブラウザでの動作再現」を目的とし、
 * .claude/TEST-HARNESS-SAFETY.md の TH1〜TH5 に従い、このランナー自身を
 * サブプロセスとして再帰的に呼び出すことは行わない（単に対象アプリの
 * 開発サーバーへHTTP/ブラウザ経由でアクセスするだけ）。
 */
const { chromium } = require("playwright");

const FRONTEND_URL = process.env.D2H_FRONTEND_URL || "http://localhost:3000";

let passed = 0;
let failed = 0;
const failures = [];

async function check(name, fn) {
  try {
    await fn();
    passed += 1;
    console.log(`  PASS - ${name}`);
  } catch (err) {
    failed += 1;
    failures.push({ name, error: err && err.message ? err.message : String(err) });
    console.log(`  FAIL - ${name}: ${err && err.message ? err.message : err}`);
  }
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg || "assertion failed");
}

async function withBrowser(fn) {
  const browser = await chromium.launch();
  try {
    const context = await browser.newContext();
    await fn(context, browser);
  } finally {
    await browser.close();
  }
}

function summary(label) {
  console.log(`\n${label}: ${passed} passed, ${failed} failed`);
  if (failures.length > 0) {
    console.log("failures:");
    for (const f of failures) console.log(`  - ${f.name}: ${f.error}`);
  }
  return failed === 0 ? 0 : 1;
}

module.exports = { FRONTEND_URL, check, assert, withBrowser, summary };
