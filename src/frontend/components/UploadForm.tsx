"use client";

import { useState, type ChangeEvent, type FormEvent } from "react";
import { createConversion, ApiError } from "@/lib/api";
import { errorMessage, messages } from "@/lib/messages";
import { InlineMessage } from "./InlineMessage";
import type { Conversion } from "@/lib/types";

export interface UploadFormProps {
  onUploaded: (conversion: Conversion) => void;
}

export function UploadForm({ onUploaded }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const conversion = await createConversion(file);
      onUploaded(conversion);
    } catch (err) {
      const code = err instanceof ApiError ? err.code : "unknown";
      setError(errorMessage(code));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <label htmlFor="design-image" className="text-sm font-medium">
        {messages.upload.fileLabel}
      </label>
      <input
        id="design-image"
        name="file"
        type="file"
        accept="image/png,image/jpeg,image/webp"
        onChange={handleFileChange}
      />
      <p className="text-xs text-zinc-500">{messages.upload.requirements}</p>

      {/* ハニーポット: 人間の利用者には見えないがBotが自動入力しうる項目 */}
      <label
        htmlFor="website"
        style={{ position: "absolute", left: "-9999px", width: 1, height: 1, overflow: "hidden" }}
      >
        {messages.upload.honeypotLabel}
      </label>
      <input
        id="website"
        name="website"
        type="text"
        tabIndex={-1}
        autoComplete="off"
        style={{ position: "absolute", left: "-9999px", width: 1, height: 1, overflow: "hidden" }}
      />

      {error && <InlineMessage kind="error" message={error} />}

      <button
        type="submit"
        disabled={!file || submitting}
        className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? messages.upload.submitting : messages.upload.submit}
      </button>
    </form>
  );
}
