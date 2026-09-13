import Link from "next/link";
import { messages } from "@/lib/messages";
import type { ConversionListItem } from "@/lib/types";

export interface ConversionListProps {
  conversions: ConversionListItem[];
}

export function ConversionList({ conversions }: ConversionListProps) {
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
          <Link href={`/conversions/${conversion.id}`} className="text-sm font-medium text-blue-700">
            {messages.upload.open}
          </Link>
        </li>
      ))}
    </ul>
  );
}
