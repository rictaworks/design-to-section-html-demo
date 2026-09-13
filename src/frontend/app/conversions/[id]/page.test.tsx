import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import ConversionPage from "./page";
import * as api from "@/lib/api";
import type { Conversion } from "@/lib/types";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "conv-1" }),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    getConversion: vi.fn(),
    getSourceImageBlob: vi.fn(),
    updateBandKind: vi.fn(),
    mergeBand: vi.fn(),
    splitBand: vi.fn(),
    removeBand: vi.fn(),
    restoreBand: vi.fn(),
    deleteConversion: vi.fn(),
  };
});

const baseConversion: Conversion = {
  id: "conv-1",
  state: "ready",
  shell_layout: "single",
  theme: "light",
  mobile_design: false,
  version: 1,
  failed_reason: null,
  bands: [
    {
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
    },
  ],
  notices: [],
  output: { html: "<p>ok</p>", byte_size: 10, version: 1 },
  source_image: { width: 1200, height: 3000, work_height: 3000 },
};

beforeEach(() => {
  vi.clearAllMocks();
  (api.getSourceImageBlob as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
    new Blob(["x"], { type: "image/png" })
  );
  if (!("createObjectURL" in URL)) {
    // @ts-expect-error jsdom does not implement this
    URL.createObjectURL = () => "blob:mock";
  }
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:mock");
});

describe("ConversionPage", () => {
  it("loads the conversion and shows its state label", async () => {
    (api.getConversion as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(baseConversion);
    render(<ConversionPage />);
    await waitFor(() => expect(screen.getByText("準備完了")).toBeInTheDocument());
  });

  it("shows the failed reason when the conversion failed", async () => {
    (api.getConversion as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ...baseConversion,
      state: "failed",
      failed_reason: "analysis_timeout",
      output: null,
    });
    render(<ConversionPage />);
    await waitFor(() => expect(screen.getByText(/analysis_timeout/)).toBeInTheDocument());
  });

  it("shows an inline error when the design image fails to load, instead of failing silently", async () => {
    (api.getConversion as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(baseConversion);
    (api.getSourceImageBlob as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("network down")
    );
    render(<ConversionPage />);
    await waitFor(() =>
      expect(screen.getByText("デザイン画像の取得に失敗しました。")).toBeInTheDocument()
    );
  });

  it("calls updateBandKind when the band list's kind select changes", async () => {
    (api.getConversion as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(baseConversion);
    (api.updateBandKind as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(baseConversion);
    render(<ConversionPage />);
    await waitFor(() => expect(screen.getByLabelText(/種別/)).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText(/種別/), { target: { value: "footer" } });

    await waitFor(() =>
      expect(api.updateBandKind).toHaveBeenCalledWith("conv-1", "b1", "footer")
    );
  });
});
