"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import {
  getConversion,
  getSourceImageBlob,
  updateBandKind,
  mergeBand,
  splitBand,
  removeBand,
  restoreBand,
  ApiError,
} from "@/lib/api";
import { errorMessage, messages } from "@/lib/messages";
import { BandOverlay } from "@/components/BandOverlay";
import { BandList } from "@/components/BandList";
import { PreviewFrame } from "@/components/PreviewFrame";
import { NoticeList } from "@/components/NoticeList";
import { InlineMessage } from "@/components/InlineMessage";
import type { Conversion, SectionKind } from "@/lib/types";

const ACTIVE_STATES = new Set(["uploaded", "analyzing", "assembling", "reassembling"]);
const POLL_INTERVAL_MS = 2000;

export default function ConversionPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [conversion, setConversion] = useState<Conversion | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const [selectedBandId, setSelectedBandId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const applyResult = useCallback((next: Conversion | undefined) => {
    if (next) setConversion(next);
  }, []);

  const handleApiCall = useCallback(
    async (call: () => Promise<Conversion>) => {
      try {
        const next = await call();
        applyResult(next);
        setError(null);
      } catch (err) {
        const code = err instanceof ApiError ? err.code : "unknown";
        setError(errorMessage(code));
      }
    },
    [applyResult]
  );

  const load = useCallback(async () => {
    try {
      const data = await getConversion(id);
      setConversion(data);
      setError(null);
    } catch (err) {
      const code = err instanceof ApiError ? err.code : "unknown";
      setError(errorMessage(code));
    }
  }, [id]);

  useEffect(() => {
    let cancelled = false;
    getConversion(id)
      .then((data) => {
        if (!cancelled) {
          setConversion(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          const code = err instanceof ApiError ? err.code : "unknown";
          setError(errorMessage(code));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    let cancelled = false;
    getSourceImageBlob(id)
      .then((blob) => {
        if (!cancelled) {
          setImageUrl(URL.createObjectURL(blob));
          setImageError(null);
        }
      })
      .catch(() => {
        // 画像取得に失敗してもオーバーレイ表示を省略するだけで結果画面自体は続行するが、
        // 理由なく黙って何も表示しないのは避け、利用者にエラーを伝える
        if (!cancelled) setImageError(messages.result.sourceImageFetchFailed);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const pollRef = useRef(load);
  useEffect(() => {
    pollRef.current = load;
  }, [load]);

  const state = conversion?.state;
  useEffect(() => {
    if (!state || !ACTIVE_STATES.has(state)) return;
    const timer = setInterval(() => pollRef.current(), POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [state]);

  function handleDownload() {
    if (!conversion?.output) return;
    const blob = new Blob([conversion.output.html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${conversion.id}-v${conversion.output.version}.html`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (!conversion) {
    return (
      <main className="mx-auto max-w-4xl px-6 py-12">
        {error && <InlineMessage kind="error" message={error} />}
      </main>
    );
  }

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-8 px-6 py-12">
      <section className="flex flex-col gap-1">
        <h1 className="text-lg font-semibold">{messages.result.statusTitle}</h1>
        <p className="text-sm">{messages.stateLabels[conversion.state]}</p>
        {conversion.failed_reason && (
          <InlineMessage
            kind="error"
            message={`${messages.result.failedReasonPrefix}${conversion.failed_reason}`}
          />
        )}
        {error && <InlineMessage kind="error" message={error} />}
      </section>

      {imageError && <InlineMessage kind="error" message={imageError} />}

      {imageUrl && (
        <BandOverlay
          imageUrl={imageUrl}
          workHeight={conversion.source_image.work_height}
          bands={conversion.bands}
          selectedBandId={selectedBandId}
          onSelectBand={setSelectedBandId}
        />
      )}

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">{messages.result.bandsTitle}</h2>
        <BandList
          bands={conversion.bands}
          selectedBandId={selectedBandId}
          onSelectBand={setSelectedBandId}
          onChangeKind={(bandId, kind: SectionKind) =>
            handleApiCall(() => updateBandKind(conversion.id, bandId, kind))
          }
          onMerge={(bandId, withBandId) =>
            handleApiCall(() => mergeBand(conversion.id, bandId, withBandId))
          }
          onSplit={(bandId, y) => handleApiCall(() => splitBand(conversion.id, bandId, y))}
          onRemove={(bandId) => handleApiCall(() => removeBand(conversion.id, bandId))}
          onRestore={(bandId) => handleApiCall(() => restoreBand(conversion.id, bandId))}
        />
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">{messages.result.noticesTitle}</h2>
        <NoticeList notices={conversion.notices} />
      </section>

      {conversion.output && (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-medium">
            {messages.result.previewTitle}（{messages.result.versionLabel} {conversion.output.version}）
          </h2>
          <PreviewFrame html={conversion.output.html} onDownload={handleDownload} />
        </section>
      )}
    </main>
  );
}
