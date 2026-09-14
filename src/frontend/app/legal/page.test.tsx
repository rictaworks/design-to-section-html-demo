import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import LegalPage from "./page";
import { messages } from "@/lib/messages";

describe("LegalPage", () => {
  it("shows the terms, disclaimer and contact sections", () => {
    render(<LegalPage />);
    expect(screen.getByRole("heading", { name: messages.legal.title })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: messages.legal.termsHeading })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: messages.legal.disclaimerHeading })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: messages.legal.contactHeading })).toBeInTheDocument();
    expect(screen.getByText(messages.legal.contact.emailValue)).toBeInTheDocument();
  });

  it("links back to the app", () => {
    render(<LegalPage />);
    const link = screen.getByRole("link", { name: messages.legal.backToApp });
    expect(link).toHaveAttribute("href", "/");
  });
});
