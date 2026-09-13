export const SECTION_KINDS = [
  "header",
  "hero",
  "features",
  "image_with_text",
  "cta",
  "pricing",
  "testimonials",
  "faq",
  "gallery",
  "logos",
  "generic_text",
  "footer",
] as const;

export type SectionKind = (typeof SECTION_KINDS)[number];

export type ConversionState =
  | "uploaded"
  | "analyzing"
  | "assembling"
  | "ready"
  | "reassembling"
  | "failed"
  | "interrupted"
  | "deleted";

export type BandState = "detected" | "overridden" | "removed" | "replaced";

export interface Band {
  id: string;
  position: number;
  top_y: number;
  bottom_y: number;
  detected_kind: SectionKind;
  user_kind: SectionKind | null;
  confidence: number;
  runner_up_kind: SectionKind | null;
  variant: string;
  state: BandState;
}

export interface Notice {
  id: string;
  notice_type: string;
  detail: string;
  band_id: string | null;
}

export interface OutputSummary {
  html: string;
  byte_size: number;
  version: number;
}

export interface SourceImageSummary {
  width: number;
  height: number;
  work_height: number;
}

export interface Conversion {
  id: string;
  state: ConversionState;
  shell_layout: "single" | "sidebar";
  theme: "light" | "dark";
  mobile_design: boolean;
  version: number;
  failed_reason: string | null;
  bands: Band[];
  notices: Notice[];
  output: OutputSummary | null;
  source_image: SourceImageSummary;
}

export interface ConversionListItem {
  id: string;
  state: ConversionState;
  created_at: string;
}

export interface ApiErrorBody {
  error: string;
}
