"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { listConversions, ApiError } from "@/lib/api";
import { errorMessage, messages } from "@/lib/messages";
import { UploadForm } from "@/components/UploadForm";
import { ConversionList } from "@/components/ConversionList";
import { InlineMessage } from "@/components/InlineMessage";
import type { Conversion, ConversionListItem } from "@/lib/types";

export default function Home() {
  const router = useRouter();
  const [conversions, setConversions] = useState<ConversionListItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listConversions()
      .then((list) => {
        if (!cancelled) {
          setConversions(list);
          setLoadError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          const code = err instanceof ApiError ? err.code : "unknown";
          setLoadError(errorMessage(code));
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function handleUploaded(conversion: Conversion) {
    router.push(`/conversions/${conversion.id}`);
  }

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-col gap-8 px-6 py-12">
      <h1 className="text-xl font-semibold">{messages.upload.title}</h1>
      <UploadForm onUploaded={handleUploaded} />

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">{messages.upload.listTitle}</h2>
        {loadError && <InlineMessage kind="error" message={loadError} />}
        <ConversionList conversions={conversions} />
      </section>
    </main>
  );
}
