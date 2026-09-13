import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PreviewFrame } from "./PreviewFrame";

describe("PreviewFrame", () => {
  it("shows all three widths at once by default, each in a sandboxed iframe without scripts", () => {
    render(<PreviewFrame html="<p>hi</p>" />);
    const frames = screen.getAllByTitle(/プレビュー/) as HTMLIFrameElement[];
    expect(frames).toHaveLength(3);
    for (const frame of frames) {
      expect(frame).toHaveAttribute("srcdoc", "<p>hi</p>");
      expect(frame.getAttribute("sandbox") ?? "").not.toContain("allow-scripts");
    }
  });

  it("switches to a single width when a width tab is clicked", () => {
    render(<PreviewFrame html="<p>hi</p>" />);
    fireEvent.click(screen.getByRole("button", { name: "モバイル" }));
    expect(screen.getAllByTitle(/プレビュー/)).toHaveLength(1);
  });

  it("calls onDownload when the download button is clicked", () => {
    const onDownload = vi.fn();
    render(<PreviewFrame html="<p>hi</p>" onDownload={onDownload} />);
    fireEvent.click(screen.getByRole("button", { name: /ダウンロード/ }));
    expect(onDownload).toHaveBeenCalled();
  });
});
