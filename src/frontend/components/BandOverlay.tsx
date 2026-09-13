import { computeOverlayRects } from "@/lib/bandOverlay";
import { messages } from "@/lib/messages";
import type { Band } from "@/lib/types";

export interface BandOverlayProps {
  imageUrl: string;
  workHeight: number;
  bands: Band[];
  selectedBandId?: string | null;
  onSelectBand: (bandId: string) => void;
}

export function BandOverlay({ imageUrl, workHeight, bands, selectedBandId, onSelectBand }: BandOverlayProps) {
  const rects = computeOverlayRects(bands, workHeight);
  const byBandId = new Map(bands.map((b) => [b.id, b]));

  return (
    <div style={{ position: "relative", width: "100%" }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={imageUrl} alt={messages.overlay.designImageAlt} style={{ width: "100%", display: "block" }} />
      {rects.map((rect) => {
        const band = byBandId.get(rect.bandId);
        if (!band) return null;
        const kind = band.user_kind ?? band.detected_kind;
        const selected = selectedBandId === band.id;
        return (
          <button
            key={band.id}
            type="button"
            data-testid={`band-region-${band.id}`}
            data-selected={selected}
            onClick={() => onSelectBand(band.id)}
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: `${rect.topPercent}%`,
              height: `${rect.heightPercent}%`,
              border: selected ? "2px solid #2563eb" : "1px dashed rgba(0,0,0,0.4)",
              background: selected ? "rgba(37,99,235,0.1)" : "transparent",
              textAlign: "left",
              padding: 0,
              cursor: "pointer",
            }}
          >
            <span
              style={{
                display: "inline-block",
                background: "rgba(0,0,0,0.7)",
                color: "#fff",
                fontSize: 11,
                padding: "1px 4px",
              }}
            >
              {messages.sectionKindLabels[kind]}
            </span>
          </button>
        );
      })}
    </div>
  );
}
