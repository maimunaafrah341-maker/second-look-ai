/**
 * Count characters the way the API does (Unicode code points), so an emoji counts once.
 * JavaScript's string length counts UTF-16 units and would count some characters twice.
 */
export function countCharacters(text: string): number {
  return [...text].length;
}

/** Format an ISO date (YYYY-MM-DD) as, for example, "6 Mar 2025", without time-zone shifts. */
export function formatDate(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!match) return iso;
  const [, year, month, day] = match;
  const date = new Date(Date.UTC(Number(year), Number(month) - 1, Number(day)));
  return new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(date);
}

export interface TextPart {
  text: string;
  highlighted: boolean;
}

/**
 * Split the original message into plain and highlighted parts for each evidence excerpt
 * that appears in it word for word. Overlapping excerpts are merged into one highlight.
 * Evidence that was shortened ("…") or whose spacing differs from the message is simply
 * not highlighted.
 */
export function highlightEvidence(message: string, evidence: string[]): TextPart[] {
  const ranges: [number, number][] = [];
  for (const excerpt of evidence) {
    if (!excerpt || excerpt.endsWith("…")) continue;
    const start = message.indexOf(excerpt);
    if (start >= 0) ranges.push([start, start + excerpt.length]);
  }
  ranges.sort((a, b) => a[0] - b[0]);

  const merged: [number, number][] = [];
  for (const [start, end] of ranges) {
    const last = merged[merged.length - 1];
    if (last && start <= last[1]) last[1] = Math.max(last[1], end);
    else merged.push([start, end]);
  }

  const parts: TextPart[] = [];
  let cursor = 0;
  for (const [start, end] of merged) {
    if (start > cursor) parts.push({ text: message.slice(cursor, start), highlighted: false });
    parts.push({ text: message.slice(start, end), highlighted: true });
    cursor = end;
  }
  if (cursor < message.length) parts.push({ text: message.slice(cursor), highlighted: false });
  return parts;
}
