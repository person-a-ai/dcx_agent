/** Crawled posts often carry long runs of blank lines; keep paragraph breaks, drop the rest. */
export function tidyText(text: string | null | undefined): string {
  return (text ?? '').replace(/\r\n?/g, '\n').replace(/\n[ \t]*(?:\n[ \t]*){2,}/g, '\n\n').trim();
}
