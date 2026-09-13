"use client";

import { useState } from "react";
import Link from "next/link";
import { messages } from "@/lib/messages";
import type { ConversionListItem } from "@/lib/types";

export interface ConversionListProps {
  conversions: ConversionListItem[];
  onDelete?: (id: string) => void;
}

function DeleteControl({ id, onDelete }: { id: string; onDelete: (id: string) => void }) {
  const [confirming, setConfirming] = useState(false);

  if (confirming) {
    return (
      <span className="flex items-center gap-2 text-xs">
        {messages.upload.deleteConfirm}
        <button
          type="button"
          onClick={() => onDelete(id)}
          className="rounded border border-red-300 px-2 py-0.5 text-red-700"
        >
          {messages.upload.deleteConfirmYes}
        </button>
        <button
          type="button"
          onClick={() => setConfirming(false)}
          className="rounded border border-zinc-300 px-2 py-0.5"
        >
          {messages.upload.deleteConfirmCancel}
        </button>
      </span>
    );
  }

  return (
    <button
      type="button"
      onClick={() => setConfirming(true)}
      className="text-sm font-medium text-red-700"
    >
      {messages.upload.delete}
    </button>
  );
}

export function ConversionList({ conversions, onDelete }: ConversionListProps) {
  if (conversions.length === 0) {
    return <p className="text-sm text-zinc-500">{messages.upload.listEmpty}</p>;
  }

  return (
    <ul className="flex flex-col gap-2">
      {conversions.map((conversion) => (
        <li
          key={conversion.id}
          className="flex items-center justify-between rounded-md border border-zinc-200 px-3 py-2"
        >
          <span className="text-sm">{messages.stateLabels[conversion.state]}</span>
          <span className="flex items-center gap-3">
            <Link href={`/conversions/${conversion.id}`} className="text-sm font-medium text-blue-700">
              {messages.upload.open}
            </Link>
            {onDelete && <DeleteControl id={conversion.id} onDelete={onDelete} />}
          </span>
        </li>
      ))}
    </ul>
  );
}
