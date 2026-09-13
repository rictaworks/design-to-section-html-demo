import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BandOverlay } from "./BandOverlay";
import type { Band } from "@/lib/types";

function band(partial: Partial<Band>): Band {
  return {
    id: "b1",
    position: 0,
    top_y: 0,
    bottom_y: 200,
    detected_kind: "hero",
    user_kind: null,
    confidence: 0.9,
    runner_up_kind: null,
    variant: "default",
    state: "detected",
    ...partial,
  };
}

describe("BandOverlay", () => {
  it("renders the design image and one overlay region per band with its kind label", () => {
    render(
      <BandOverlay
        imageUrl="data:image/png;base64,AAA"
        workHeight={1000}
        bands={[band({ id: "b1", top_y: 0, bottom_y: 200, detected_kind: "hero" })]}
        onSelectBand={vi.fn()}
      />
    );
    expect(screen.getByRole("img", { name: /デザイン画像/ })).toBeInTheDocument();
    expect(screen.getByText("ヒーロー")).toBeInTheDocument();
  });

  it("calls onSelectBand when an overlay region is clicked, and highlights the selected band", () => {
    const onSelectBand = vi.fn();
    render(
      <BandOverlay
        imageUrl="data:image/png;base64,AAA"
        workHeight={1000}
        bands={[band({ id: "b1" })]}
        selectedBandId="b1"
        onSelectBand={onSelectBand}
      />
    );
    fireEvent.click(screen.getByTestId("band-region-b1"));
    expect(onSelectBand).toHaveBeenCalledWith("b1");
    expect(screen.getByTestId("band-region-b1")).toHaveAttribute("data-selected", "true");
  });
});
