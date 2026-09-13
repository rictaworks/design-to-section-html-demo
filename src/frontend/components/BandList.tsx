"use client";

import { useState } from "react";
import { messages } from "@/lib/messages";
import { SECTION_KINDS, type Band, type SectionKind } from "@/lib/types";

export interface BandListProps {
  bands: Band[];
  selectedBandId?: string | null;
  onSelectBand?: (bandId: string) => void;
  onChangeKind: (bandId: string, kind: SectionKind) => void;
  onMerge: (bandId: string, withBandId: string) => void;
  onSplit: (bandId: string, y: number) => void;
  onRemove: (bandId: string) => void;
  onRestore: (bandId: string) => void;
}

function SplitControl({ bandId, onSplit }: { bandId: string; onSplit: (bandId: string, y: number) => void }) {
  const [y, setY] = useState("");
  return (
    <div className="flex items-center gap-2">
      <label htmlFor={`split-y-${bandId}`} className="text-xs">
        {messages.result.splitPositionLabel}
      </label>
      <input
        id={`split-y-${bandId}`}
        type="number"
        value={y}
        onChange={(e) => setY(e.target.value)}
        className="w-20 rounded border border-zinc-300 px-1 py-0.5 text-xs"
      />
      <button
        type="button"
        onClick={() => y !== "" && onSplit(bandId, Number(y))}
        className="rounded border border-zinc-300 px-2 py-0.5 text-xs"
      >
        {messages.result.split}
      </button>
    </div>
  );
}

export function BandList({
  bands,
  selectedBandId,
  onSelectBand,
  onChangeKind,
  onMerge,
  onSplit,
  onRemove,
  onRestore,
}: BandListProps) {
  const sorted = [...bands].sort((a, b) => a.position - b.position);

  return (
    <ul className="flex flex-col gap-3">
      {sorted.map((band, index) => {
        const kind = band.user_kind ?? band.detected_kind;
        const next = sorted[index + 1];
        const removed = band.state === "removed";
        return (
          <li
            key={band.id}
            onClick={() => onSelectBand?.(band.id)}
            className={`flex flex-col gap-2 rounded-md border px-3 py-2 ${
              selectedBandId === band.id ? "border-blue-500" : "border-zinc-200"
            }`}
          >
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <span className="font-medium">{messages.sectionKindLabels[kind]}</span>
              <span className="text-zinc-500">
                {messages.result.confidenceLabel}: {Math.round(band.confidence * 100)}%
              </span>
              <span className="text-zinc-500">
                {messages.result.variantLabel}: {band.variant}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <label htmlFor={`kind-${band.id}`} className="text-xs">
                {messages.result.changeKind}
              </label>
              <select
                id={`kind-${band.id}`}
                value={kind}
                onChange={(e) => onChangeKind(band.id, e.target.value as SectionKind)}
                className="rounded border border-zinc-300 px-1 py-0.5 text-xs"
              >
                {SECTION_KINDS.map((k) => (
                  <option key={k} value={k}>
                    {messages.sectionKindLabels[k]}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {next && !removed && next.state !== "removed" && (
                <button
                  type="button"
                  onClick={() => onMerge(band.id, next.id)}
                  className="rounded border border-zinc-300 px-2 py-0.5 text-xs"
                >
                  {messages.result.merge}
                </button>
              )}
              {!removed && <SplitControl bandId={band.id} onSplit={onSplit} />}
              {removed ? (
                <button
                  type="button"
                  onClick={() => onRestore(band.id)}
                  className="rounded border border-zinc-300 px-2 py-0.5 text-xs"
                >
                  {messages.result.restore}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => onRemove(band.id)}
                  className="rounded border border-zinc-300 px-2 py-0.5 text-xs"
                >
                  {messages.result.remove}
                </button>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
