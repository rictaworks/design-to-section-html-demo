import type { Band } from "./types";

export interface OverlayRect {
  bandId: string;
  topPercent: number;
  heightPercent: number;
}

export function computeOverlayRects(bands: Band[], workHeight: number): OverlayRect[] {
  if (workHeight <= 0) {
    throw new Error("workHeight must be positive");
  }
  return bands.map((b) => ({
    bandId: b.id,
    topPercent: (b.top_y / workHeight) * 100,
    heightPercent: ((b.bottom_y - b.top_y) / workHeight) * 100,
  }));
}
