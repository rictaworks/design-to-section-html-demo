import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ConversionList } from "./ConversionList";
import type { ConversionListItem } from "@/lib/types";

describe("ConversionList", () => {
  it("shows the empty message when there are no conversions", () => {
    render(<ConversionList conversions={[]} />);
    expect(screen.getByText("まだ変換がありません。")).toBeInTheDocument();
  });

  it("renders each conversion with its state label and a link to the result page", () => {
    const items: ConversionListItem[] = [
      { id: "abc", state: "ready", created_at: "2026-01-01T00:00:00Z" },
      { id: "def", state: "analyzing", created_at: "2026-01-02T00:00:00Z" },
    ];
    render(<ConversionList conversions={items} />);

    expect(screen.getByText("準備完了")).toBeInTheDocument();
    expect(screen.getByText("解析中")).toBeInTheDocument();
    const links = screen.getAllByRole("link");
    expect(links[0]).toHaveAttribute("href", "/conversions/abc");
    expect(links[1]).toHaveAttribute("href", "/conversions/def");
  });
});
