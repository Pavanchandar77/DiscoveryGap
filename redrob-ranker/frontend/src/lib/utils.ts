import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Compact integer formatting with thousands separators (e.g. 23366 -> "23,366"). */
export function formatInt(value: number): string {
  return Math.round(value).toLocaleString('en-US');
}

/**
 * Talent Mispricing Index — the number of positions the ATS undervalues a
 * candidate by (ats_rank - our_rank). Rendered as a signed, whole-number
 * position delta, never a multiple.
 */
export function formatTmi(value: number): string {
  const rounded = Math.round(value);
  return `${rounded > 0 ? '+' : ''}${rounded.toLocaleString('en-US')}`;
}
