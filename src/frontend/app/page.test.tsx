import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { AppRouterContext } from "next/dist/shared/lib/app-router-context.shared-runtime";
import Home from "./page";
import * as api from "@/lib/api";

const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  refresh: vi.fn(),
  prefetch: vi.fn(),
} as unknown as import("next/dist/shared/lib/app-router-context.shared-runtime").AppRouterInstance;

function renderHome() {
  return render(
    <AppRouterContext.Provider value={mockRouter}>
      <Home />
    </AppRouterContext.Provider>
  );
}

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, listConversions: vi.fn(), createConversion: vi.fn(), deleteConversion: vi.fn() };
});

beforeEach(() => {
  vi.clearAllMocks();
});

describe("Home page", () => {
  it("loads and shows the conversion list on mount", async () => {
    (api.listConversions as unknown as ReturnType<typeof vi.fn>).mockResolvedValue([
      { id: "abc", state: "ready", created_at: "2026-01-01T00:00:00Z" },
    ]);
    renderHome();

    await waitFor(() => expect(screen.getByText("準備完了")).toBeInTheDocument());
  });

  it("renders the upload form", async () => {
    (api.listConversions as unknown as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    renderHome();
    expect(screen.getByRole("button", { name: /変換する/ })).toBeInTheDocument();
    await waitFor(() => expect(api.listConversions).toHaveBeenCalled());
  });

  it("deletes a conversion after inline confirmation and removes it from the list", async () => {
    (api.listConversions as unknown as ReturnType<typeof vi.fn>).mockResolvedValue([
      { id: "abc", state: "ready", created_at: "2026-01-01T00:00:00Z" },
    ]);
    (api.deleteConversion as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
    renderHome();
    await waitFor(() => expect(screen.getByText("準備完了")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "削除" }));
    fireEvent.click(screen.getByRole("button", { name: "削除する" }));

    await waitFor(() => expect(api.deleteConversion).toHaveBeenCalledWith("abc"));
    await waitFor(() => expect(screen.getByText("まだ変換がありません。")).toBeInTheDocument());
  });
});
