import { describe, it, expect } from "vitest";
import { computeOverlayRects } from "./bandOverlay";
import type { Band } from "./types";

function band(partial: Partial<Band>): Band {
  return {
    id: "b",
    position: 0,
    top_y: 0,
    bottom_y: 100,
    detected_kind: "hero",
    user_kind: null,
    confidence: 0.9,
    runner_up_kind: null,
    variant: "default",
    state: "detected",
    ...partial,
  };
}

describe("computeOverlayRects", () => {
  it("maps work-coordinate band ranges to percentage rects over the displayed image", () => {
    const bands = [band({ id: "1", top_y: 0, bottom_y: 200 }), band({ id: "2", top_y: 200, bottom_y: 1000 })];

    const rects = computeOverlayRects(bands, 1000);

    expect(rects).toEqual([
      { bandId: "1", topPercent: 0, heightPercent: 20 },
      { bandId: "2", topPercent: 20, heightPercent: 80 },
    ]);
  });

  it("returns an empty list for an empty band list", () => {
    expect(computeOverlayRects([], 1000)).toEqual([]);
  });

  it("throws when workHeight is zero or negative", () => {
    expect(() => computeOverlayRects([band({})], 0)).toThrow();
    expect(() => computeOverlayRects([band({})], -1)).toThrow();
  });
});
