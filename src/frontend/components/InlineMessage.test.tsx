import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { InlineMessage } from "./InlineMessage";

describe("InlineMessage", () => {
  it("renders an alert role for error kind", () => {
    render(<InlineMessage kind="error" message="失敗しました" />);
    expect(screen.getByRole("alert")).toHaveTextContent("失敗しました");
  });

  it("renders a status role for info kind", () => {
    render(<InlineMessage kind="info" message="お知らせ" />);
    expect(screen.getByRole("status")).toHaveTextContent("お知らせ");
  });
});
