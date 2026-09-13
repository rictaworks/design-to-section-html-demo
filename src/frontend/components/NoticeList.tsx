import { messages } from "@/lib/messages";
import type { Notice } from "@/lib/types";

export interface NoticeListProps {
  notices: Notice[];
}

export function NoticeList({ notices }: NoticeListProps) {
  if (notices.length === 0) {
    return <p className="text-sm text-zinc-500">{messages.result.noticesEmpty}</p>;
  }

  return (
    <ul className="flex flex-col gap-1">
      {notices.map((notice) => (
        <li key={notice.id} className="text-sm text-amber-800">
          {notice.detail}
        </li>
      ))}
    </ul>
  );
}
