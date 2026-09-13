import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { NoticeList } from "./NoticeList";
import type { Notice } from "@/lib/types";

describe("NoticeList", () => {
  it("shows the empty message when there are no notices", () => {
    render(<NoticeList notices={[]} />);
    expect(screen.getByText("注意事項はありません。")).toBeInTheDocument();
  });

  it("renders Japanese text derived from notice_type, not the raw detail object", () => {
    const notices: Notice[] = [
      { id: "n1", notice_type: "low_confidence_kind", detail: { kind: "hero" }, band_id: "b1" },
    ];
    render(<NoticeList notices={notices} />);
    expect(screen.getByText(/信頼度/)).toBeInTheDocument();
  });

  it("does not throw when detail is a non-empty object (regression: React cannot render objects as children)", () => {
    const notices: Notice[] = [
      {
        id: "n2",
        notice_type: "close_confidence_runner_up",
        detail: { runner_up_kind: "features" },
        band_id: "b2",
      },
    ];
    expect(() => render(<NoticeList notices={notices} />)).not.toThrow();
    expect(screen.getByText(/特徴一覧/)).toBeInTheDocument();
  });

  it("falls back to a generic message for an unknown notice_type instead of crashing", () => {
    const notices: Notice[] = [
      { id: "n3", notice_type: "something_new", detail: { foo: "bar" }, band_id: null },
    ];
    expect(() => render(<NoticeList notices={notices} />)).not.toThrow();
  });
});
