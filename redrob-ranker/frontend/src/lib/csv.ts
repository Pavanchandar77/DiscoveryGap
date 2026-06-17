import { Candidate } from '../types';

/**
 * Builds the 4-column submission CSV from the dashboard cards.
 * Hard-rule columns (see FRONTEND_CONTRACT.md):
 *   candidate_id, rank (= our_rank), score (= fit / 100), reasoning
 * Rows are ordered by our_rank ascending.
 */
export function buildSubmissionCsv(cards: Candidate[]): string {
  const header = ['candidate_id', 'rank', 'score', 'reasoning'];
  const rows = [...cards]
    .sort((a, b) => a.our_rank - b.our_rank)
    .map((c) => [
      c.candidate_id,
      String(c.our_rank),
      (c.fit / 100).toString(),
      c.reasoning ?? '',
    ]);

  return [header, ...rows].map((row) => row.map(escapeCell).join(',')).join('\r\n');
}

/** RFC-4180 escaping: wrap in quotes and double any embedded quotes when needed. */
function escapeCell(value: string): string {
  if (/[",\r\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

/** Triggers a client-side download of the given CSV text. */
export function downloadCsv(filename: string, csv: string): void {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
