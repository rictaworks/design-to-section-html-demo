export const PREVIEW_WIDTHS = {
  mobile: 375,
  tablet: 768,
  desktop: 1280,
} as const;

export type PreviewWidthKey = keyof typeof PREVIEW_WIDTHS;
