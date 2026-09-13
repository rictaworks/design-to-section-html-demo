import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  listConversions,
  createConversion,
  getConversion,
  deleteConversion,
  updateBandKind,
  mergeBand,
  splitBand,
  removeBand,
  restoreBand,
  getSourceImageBlob,
  ApiError,
} from "./api";

const BACKEND = "http://backend.test";

beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_BACKEND_URL", BACKEND);
  vi.stubGlobal("fetch", vi.fn());
});

describe("listConversions", () => {
  it("GETs /conversions with credentials included", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify([{ id: "1", state: "ready", created_at: "x" }]), {
        status: 200,
      })
    );

    const result = await listConversions();

    expect(fetch).toHaveBeenCalledWith(
      `${BACKEND}/conversions`,
      expect.objectContaining({ credentials: "include" })
    );
    expect(result).toEqual([{ id: "1", state: "ready", created_at: "x" }]);
  });
});

describe("createConversion", () => {
  it("POSTs multipart form data including honeypot field", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ id: "1", state: "uploaded" }), { status: 201 })
    );
    const file = new File(["abc"], "design.png", { type: "image/png" });

    await createConversion(file);

    const call = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(call[0]).toBe(`${BACKEND}/conversions`);
    const init = call[1] as RequestInit;
    expect(init.credentials).toBe("include");
    const body = init.body as FormData;
    expect(body.get("file")).toBe(file);
    expect(body.get("website")).toBe("");
  });

  it("throws ApiError with backend error code on failure", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockImplementation(
      async () => new Response(JSON.stringify({ error: "size_exceeded" }), { status: 422 })
    );
    const file = new File(["abc"], "design.png", { type: "image/png" });

    await expect(createConversion(file)).rejects.toThrow(ApiError);
    await expect(createConversion(file)).rejects.toMatchObject({ code: "size_exceeded" });
  });
});

describe("getConversion", () => {
  it("GETs /conversions/:id", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ id: "1" }), { status: 200 })
    );
    await getConversion("1");
    expect(fetch).toHaveBeenCalledWith(
      `${BACKEND}/conversions/1`,
      expect.objectContaining({ credentials: "include" })
    );
  });

  it("throws not_found ApiError on 404", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ error: "not_found" }), { status: 404 })
    );
    await expect(getConversion("x")).rejects.toMatchObject({ code: "not_found" });
  });
});

describe("getSourceImageBlob", () => {
  it("GETs the binary source image with credentials included", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response("abc", { status: 200, headers: { "Content-Type": "image/png" } })
    );

    const result = await getSourceImageBlob("1");

    expect(fetch).toHaveBeenCalledWith(
      `${BACKEND}/conversions/1/source_image`,
      expect.objectContaining({ credentials: "include" })
    );
    expect(result.type).toBe("image/png");
  });

  it("throws ApiError on failure", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ error: "not_found" }), { status: 404 })
    );
    await expect(getSourceImageBlob("x")).rejects.toMatchObject({ code: "not_found" });
  });
});

describe("deleteConversion", () => {
  it("DELETEs /conversions/:id", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(new Response(null, { status: 204 }));
    await deleteConversion("1");
    expect(fetch).toHaveBeenCalledWith(
      `${BACKEND}/conversions/1`,
      expect.objectContaining({ method: "DELETE", credentials: "include" })
    );
  });
});

describe("band operations", () => {
  beforeEach(() => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ id: "1" }), { status: 200 })
    );
  });

  it("updateBandKind PATCHes with kind", async () => {
    await updateBandKind("1", "b1", "hero");
    const call = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(call[0]).toBe(`${BACKEND}/conversions/1/bands/b1`);
    expect((call[1] as RequestInit).method).toBe("PATCH");
    expect(JSON.parse((call[1] as RequestInit).body as string)).toEqual({ kind: "hero" });
  });

  it("mergeBand POSTs with with-band id", async () => {
    await mergeBand("1", "b1", "b2");
    const call = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(call[0]).toBe(`${BACKEND}/conversions/1/bands/b1/merge`);
    expect(JSON.parse((call[1] as RequestInit).body as string)).toEqual({ with: "b2" });
  });

  it("splitBand POSTs with y", async () => {
    await splitBand("1", "b1", 120);
    const call = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(call[0]).toBe(`${BACKEND}/conversions/1/bands/b1/split`);
    expect(JSON.parse((call[1] as RequestInit).body as string)).toEqual({ y: 120 });
  });

  it("removeBand POSTs to /remove", async () => {
    await removeBand("1", "b1");
    const call = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(call[0]).toBe(`${BACKEND}/conversions/1/bands/b1/remove`);
    expect((call[1] as RequestInit).method).toBe("POST");
  });

  it("restoreBand POSTs to /restore", async () => {
    await restoreBand("1", "b1");
    const call = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(call[0]).toBe(`${BACKEND}/conversions/1/bands/b1/restore`);
    expect((call[1] as RequestInit).method).toBe("POST");
  });
});
