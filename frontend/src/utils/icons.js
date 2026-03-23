/**
 * SVG Icon Library — Inline SVG icons for the dashboard.
 * Each function returns an SVG string. Pass `size` (px) and `color` (CSS color).
 */

const d = (size = 18, color = 'currentColor') => `width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"`;

// ── Navigation Icons ──────────────────────────────────────────
export const iconOverview = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>`;

export const iconSentiment = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><circle cx="12" cy="12" r="10"/><path d="M12 8v4l2 2"/></svg>`;

export const iconSearch = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`;

export const iconReport = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`;

export const iconGlobe = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>`;

// ── KPI / Stat Icons ──────────────────────────────────────────
export const iconNewspaper = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 0-2 0z"/><path d="M2 10h4"/><path d="M2 14h4"/><path d="M2 18h4"/><line x1="10" y1="6" x2="18" y2="6"/><line x1="10" y1="10" x2="18" y2="10"/><line x1="10" y1="14" x2="14" y2="14"/></svg>`;

export const iconTarget = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>`;

export const iconRadio = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.07"/><path d="M13.06 7.72A14.9 14.9 0 0 1 19 12"/><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>`;

export const iconScan = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><circle cx="12" cy="12" r="3"/></svg>`;

export const iconTag = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>`;

// ── Directional / Action Icons ────────────────────────────────
export const iconArrowUp = (s = 14, c = 'currentColor') =>
  `<svg ${d(s,c)}><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>`;

export const iconArrowDown = (s = 14, c = 'currentColor') =>
  `<svg ${d(s,c)}><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>`;

export const iconTrendUp = (s = 14, c = 'currentColor') =>
  `<svg ${d(s,c)}><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>`;

export const iconTrendDown = (s = 14, c = 'currentColor') =>
  `<svg ${d(s,c)}><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>`;

export const iconChevronDown = (s = 14, c = 'currentColor') =>
  `<svg ${d(s,c)}><polyline points="6 9 12 15 18 9"/></svg>`;

// ── Misc Icons ────────────────────────────────────────────────
export const iconBell = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>`;

export const iconBarChart = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`;

export const iconPieChart = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>`;

export const iconActivity = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`;

export const iconLive = (s = 8, c = '#3FB950') =>
  `<svg width="${s}" height="${s}" viewBox="0 0 8 8"><circle cx="4" cy="4" r="4" fill="${c}"><animate attributeName="opacity" values="1;0.4;1" dur="2s" repeatCount="indefinite"/></circle></svg>`;

export const iconMap = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>`;

export const iconClipboard = (s = 18, c = 'currentColor') =>
  `<svg ${d(s,c)}><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>`;

// ── Country/Region Flag Icons (styled circles with region codes) ──
export const iconFlag = (code = '', s = 18) => {
  const colors = {
    'es': '#FF6B6B', 'hi': '#FFD93D', 'pt': '#6BCB77',
    'ru': '#BC8CFF', 'ja': '#58A6FF', 'sw': '#FF8C42',
  };
  const bg = colors[code] || '#8b919d';
  return `<svg width="${s}" height="${s}" viewBox="0 0 20 20"><circle cx="10" cy="10" r="10" fill="${bg}" opacity="0.2"/><circle cx="10" cy="10" r="7" fill="${bg}" opacity="0.4"/><text x="10" y="14" text-anchor="middle" fill="${bg}" font-size="9" font-weight="700" font-family="Inter,sans-serif">${code.toUpperCase()}</text></svg>`;
};
