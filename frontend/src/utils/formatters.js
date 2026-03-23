/** Format polarity as +/-  with 2 decimals */
export function formatPolarity(val) {
  const n = parseFloat(val);
  if (isNaN(n)) return '0.00';
  return (n >= 0 ? '+' : '') + n.toFixed(2);
}

/** Return 'Positive', 'Neutral', or 'Negative' */
export function sentimentLabel(polarity) {
  const n = parseFloat(polarity);
  if (n > 0.05) return 'Positive';
  if (n < -0.05) return 'Negative';
  return 'Neutral';
}

/** Return CSS class for sentiment */
export function sentimentClass(polarity) {
  const label = sentimentLabel(polarity);
  return `badge--${label.toLowerCase()}`;
}

/** Format date string "2025_10_01" → "Oct 1, 2025" */
export function formatDate(dateStr) {
  if (!dateStr) return '';
  const parts = String(dateStr).split('_');
  if (parts.length !== 3) return dateStr;
  const date = new Date(parts[0], parts[1] - 1, parts[2]);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

/** Format date string "2025_10_01" → "Mon" day name */
export function formatDayName(dateStr) {
  if (!dateStr) return '';
  const parts = String(dateStr).split('_');
  if (parts.length !== 3) return dateStr;
  const date = new Date(parts[0], parts[1] - 1, parts[2]);
  return date.toLocaleDateString('en-US', { weekday: 'long' });
}

/** Compact number: 1200 → 1.2K */
export function compactNumber(num) {
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return String(num);
}

/** Truncate text */
export function truncate(str, len = 60) {
  if (!str) return '';
  return str.length > len ? str.slice(0, len) + '…' : str;
}

/** Percentage */
export function pct(value, total) {
  if (!total) return '0%';
  return Math.round((value / total) * 100) + '%';
}
