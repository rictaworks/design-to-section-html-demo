import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCircleExclamation, faCircleInfo } from "@fortawesome/free-solid-svg-icons";

export interface InlineMessageProps {
  kind: "error" | "info";
  message: string;
}

export function InlineMessage({ kind, message }: InlineMessageProps) {
  const isError = kind === "error";
  return (
    <div
      role={isError ? "alert" : "status"}
      className={`flex items-start gap-2 rounded-md border px-3 py-2 text-sm ${
        isError
          ? "border-red-300 bg-red-50 text-red-800"
          : "border-blue-300 bg-blue-50 text-blue-800"
      }`}
    >
      <FontAwesomeIcon icon={isError ? faCircleExclamation : faCircleInfo} className="mt-0.5" />
      <span>{message}</span>
    </div>
  );
}
