import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BandList } from "./BandList";
import type { Band } from "@/lib/types";

function band(partial: Partial<Band>): Band {
  return {
    id: "b1",
    position: 0,
    top_y: 0,
    bottom_y: 100,
    detected_kind: "hero",
    user_kind: null,
    confidence: 0.8,
    runner_up_kind: null,
    variant: "default",
    state: "detected",
    ...partial,
  };
}

describe("BandList", () => {
  it("renders kind label, confidence and variant for each band", () => {
    render(
      <BandList
        bands={[band({ id: "b1", detected_kind: "hero", confidence: 0.82, variant: "image-right" })]}
        onChangeKind={vi.fn()}
        onMerge={vi.fn()}
        onSplit={vi.fn()}
        onRemove={vi.fn()}
        onRestore={vi.fn()}
      />
    );
    expect(screen.getAllByText("ヒーロー").length).toBeGreaterThan(0);
    expect(screen.getByText(/82%/)).toBeInTheDocument();
    expect(screen.getByText(/image-right/)).toBeInTheDocument();
  });

  it("calls onChangeKind when the kind select changes", () => {
    const onChangeKind = vi.fn();
    render(
      <BandList
        bands={[band({ id: "b1" })]}
        onChangeKind={onChangeKind}
        onMerge={vi.fn()}
        onSplit={vi.fn()}
        onRemove={vi.fn()}
        onRestore={vi.fn()}
      />
    );
    fireEvent.change(screen.getByLabelText(/種別/), { target: { value: "footer" } });
    expect(onChangeKind).toHaveBeenCalledWith("b1", "footer");
  });

  it("calls onMerge with the current and next band ids", () => {
    const onMerge = vi.fn();
    render(
      <BandList
        bands={[band({ id: "b1", position: 0 }), band({ id: "b2", position: 1 })]}
        onChangeKind={vi.fn()}
        onMerge={onMerge}
        onSplit={vi.fn()}
        onRemove={vi.fn()}
        onRestore={vi.fn()}
      />
    );
    fireEvent.click(screen.getAllByRole("button", { name: "次の帯と結合" })[0]);
    expect(onMerge).toHaveBeenCalledWith("b1", "b2");
  });

  it("does not offer merging into a next band that has been removed", () => {
    const onMerge = vi.fn();
    render(
      <BandList
        bands={[band({ id: "b1", position: 0 }), band({ id: "b2", position: 1, state: "removed" })]}
        onChangeKind={vi.fn()}
        onMerge={onMerge}
        onSplit={vi.fn()}
        onRemove={vi.fn()}
        onRestore={vi.fn()}
      />
    );
    expect(screen.queryByRole("button", { name: "次の帯と結合" })).not.toBeInTheDocument();
  });

  it("calls onSplit with the entered y position", () => {
    const onSplit = vi.fn();
    render(
      <BandList
        bands={[band({ id: "b1" })]}
        onChangeKind={vi.fn()}
        onMerge={vi.fn()}
        onSplit={onSplit}
        onRemove={vi.fn()}
        onRestore={vi.fn()}
      />
    );
    fireEvent.change(screen.getByLabelText(/分割位置/), { target: { value: "60" } });
    fireEvent.click(screen.getByRole("button", { name: "分割" }));
    expect(onSplit).toHaveBeenCalledWith("b1", 60);
  });

  it("shows a restore button instead of remove when the band is removed", () => {
    const onRestore = vi.fn();
    render(
      <BandList
        bands={[band({ id: "b1", state: "removed" })]}
        onChangeKind={vi.fn()}
        onMerge={vi.fn()}
        onSplit={vi.fn()}
        onRemove={vi.fn()}
        onRestore={onRestore}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: "復元" }));
    expect(onRestore).toHaveBeenCalledWith("b1");
  });
});
