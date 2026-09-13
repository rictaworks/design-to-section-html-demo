import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { UploadForm } from "./UploadForm";
import * as api from "@/lib/api";
import { ApiError } from "@/lib/api";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, createConversion: vi.fn() };
});

beforeEach(() => {
  vi.clearAllMocks();
});

function selectFile() {
  const file = new File(["abc"], "design.png", { type: "image/png" });
  const input = screen.getByLabelText(/デザイン画像/) as HTMLInputElement;
  fireEvent.change(input, { target: { files: [file] } });
  return file;
}

describe("UploadForm", () => {
  it("includes an offscreen honeypot input named website", () => {
    render(<UploadForm onUploaded={vi.fn()} />);
    const honeypot = document.querySelector('input[name="website"]') as HTMLInputElement;
    expect(honeypot).toBeInTheDocument();
    expect(honeypot).toHaveAttribute("tabindex", "-1");
    expect(honeypot).toHaveAttribute("autocomplete", "off");
  });

  it("submits whatever value was actually entered in the honeypot field, not a hardcoded empty string", async () => {
    (api.createConversion as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: "1",
      state: "uploaded",
    } as unknown as Awaited<ReturnType<typeof api.createConversion>>);
    render(<UploadForm onUploaded={vi.fn()} />);

    selectFile();
    const honeypot = document.querySelector('input[name="website"]') as HTMLInputElement;
    fireEvent.change(honeypot, { target: { value: "http://spam.example" } });
    fireEvent.click(screen.getByRole("button", { name: /変換する/ }));

    await waitFor(() =>
      expect(api.createConversion).toHaveBeenCalledWith(expect.anything(), "http://spam.example")
    );
  });

  it("calls createConversion and onUploaded on successful submit", async () => {
    const conversion = { id: "1", state: "uploaded" } as unknown as Awaited<
      ReturnType<typeof api.createConversion>
    >;
    (api.createConversion as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(conversion);
    const onUploaded = vi.fn();
    render(<UploadForm onUploaded={onUploaded} />);

    selectFile();
    fireEvent.click(screen.getByRole("button", { name: /変換する/ }));

    await waitFor(() => expect(onUploaded).toHaveBeenCalledWith(conversion));
  });

  it("shows an inline error message (not a native alert) on failure", async () => {
    (api.createConversion as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(
      new ApiError("size_exceeded", 422)
    );
    render(<UploadForm onUploaded={vi.fn()} />);

    selectFile();
    fireEvent.click(screen.getByRole("button", { name: /変換する/ }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent("10MBの上限")
    );
  });
});
