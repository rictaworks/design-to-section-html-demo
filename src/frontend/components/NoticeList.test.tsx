import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { NoticeList } from "./NoticeList";
import type { Notice } from "@/lib/types";

describe("NoticeList", () => {
  it("shows the empty message when there are no notices", () => {
    render(<NoticeList notices={[]} />);
    expect(screen.getByText("注意事項はありません。")).toBeInTheDocument();
  });

  it("renders each notice's detail text", () => {
    const notices: Notice[] = [
      { id: "n1", notice_type: "low_confidence_kind", detail: "信頼度が低いため採用しました。", band_id: "b1" },
    ];
    render(<NoticeList notices={notices} />);
    expect(screen.getByText("信頼度が低いため採用しました。")).toBeInTheDocument();
  });
});
