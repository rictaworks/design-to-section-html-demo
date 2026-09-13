import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
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

  it("asks for inline confirmation (not a native confirm()) before deleting, and calls onDelete only after confirming", () => {
    const onDelete = vi.fn();
    render(
      <ConversionList
        conversions={[{ id: "abc", state: "ready", created_at: "2026-01-01T00:00:00Z" }]}
        onDelete={onDelete}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "削除" }));
    expect(onDelete).not.toHaveBeenCalled();
    expect(screen.getByText("この変換を削除しますか？")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "削除する" }));
    expect(onDelete).toHaveBeenCalledWith("abc");
  });

  it("cancels the inline confirmation without calling onDelete", () => {
    const onDelete = vi.fn();
    render(
      <ConversionList
        conversions={[{ id: "abc", state: "ready", created_at: "2026-01-01T00:00:00Z" }]}
        onDelete={onDelete}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "削除" }));
    fireEvent.click(screen.getByRole("button", { name: "キャンセル" }));

    expect(onDelete).not.toHaveBeenCalled();
    expect(screen.queryByText("この変換を削除しますか？")).not.toBeInTheDocument();
  });
});
