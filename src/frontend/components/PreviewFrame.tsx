"use client";

import { useState } from "react";
import { messages } from "@/lib/messages";
import { PREVIEW_WIDTHS, type PreviewWidthKey } from "@/lib/previewWidths";

export interface PreviewFrameProps {
  html: string;
  onDownload?: () => void;
}

const WIDTH_LABELS: Record<PreviewWidthKey, string> = {
  mobile: messages.result.previewMobile,
  tablet: messages.result.previewTablet,
  desktop: messages.result.previewDesktop,
};

export function PreviewFrame({ html, onDownload }: PreviewFrameProps) {
  const [selected, setSelected] = useState<PreviewWidthKey | "all">("all");
  const keys = Object.keys(PREVIEW_WIDTHS) as PreviewWidthKey[];
  const visible = selected === "all" ? keys : [selected];

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setSelected("all")}
          className={`rounded border px-2 py-1 text-xs ${selected === "all" ? "border-blue-500" : "border-zinc-300"}`}
        >
          {messages.result.previewTitle}
        </button>
        {keys.map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => setSelected(key)}
            className={`rounded border px-2 py-1 text-xs ${selected === key ? "border-blue-500" : "border-zinc-300"}`}
          >
            {WIDTH_LABELS[key]}
          </button>
        ))}
        {onDownload && (
          <button
            type="button"
            onClick={onDownload}
            className="ml-auto rounded bg-zinc-900 px-3 py-1 text-xs text-white"
          >
            {messages.result.download}
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-4">
        {visible.map((key) => (
          <div key={key} className="flex flex-col gap-1">
            <span className="text-xs text-zinc-500">{WIDTH_LABELS[key]}</span>
            <iframe
              title={`${WIDTH_LABELS[key]}${messages.result.previewTitle}`}
              srcDoc={html}
              sandbox=""
              style={{ width: PREVIEW_WIDTHS[key], height: 600, border: "1px solid #e4e4e7" }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
