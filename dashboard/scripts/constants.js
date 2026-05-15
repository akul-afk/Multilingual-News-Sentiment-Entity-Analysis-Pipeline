/** Design tokens — mirrors the CSS custom properties */
export const COLORS = {
  get bg() { return getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || '#f4ecd8'; },
  get surface() { return getComputedStyle(document.documentElement).getPropertyValue('--surface').trim() || '#ffffff'; },
  get surfaceLow() { return getComputedStyle(document.documentElement).getPropertyValue('--surface-low').trim() || '#ebe1c5'; },
  get surfaceHigh() { return getComputedStyle(document.documentElement).getPropertyValue('--surface-high').trim() || '#ffffff'; },
  get surfaceHighest() { return getComputedStyle(document.documentElement).getPropertyValue('--surface-highest').trim() || '#fdfaf2'; },
  get surfaceLowest() { return getComputedStyle(document.documentElement).getPropertyValue('--surface-lowest').trim() || '#e2d8b8'; },
  get primary() { return getComputedStyle(document.documentElement).getPropertyValue('--primary').trim() || '#8b0000'; },
  get primaryLight() { return getComputedStyle(document.documentElement).getPropertyValue('--primary-light').trim() || '#b22222'; },
  get secondary() { return getComputedStyle(document.documentElement).getPropertyValue('--secondary').trim() || '#2f4f4f'; },
  get tertiary() { return getComputedStyle(document.documentElement).getPropertyValue('--tertiary').trim() || '#1b4d3e'; },
  get error() { return getComputedStyle(document.documentElement).getPropertyValue('--error').trim() || '#8b0000'; },
  get text() { return getComputedStyle(document.documentElement).getPropertyValue('--text').trim() || '#1a1a1a'; },
  get textMuted() { return getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#3d3d3d'; },
  get textDim() { return getComputedStyle(document.documentElement).getPropertyValue('--text-dim').trim() || '#5c5c5c'; },
  get outline() { return getComputedStyle(document.documentElement).getPropertyValue('--outline').trim() || '#1a1a1a'; },
};

/** Source label to region info */
export const SOURCE_REGIONS = {
  'BBC Spanish':    { region: 'Latin America',  code: 'es', lat: 19.43,  lng: -99.13 },
  'BBC Hindi':      { region: 'South Asia',     code: 'hi', lat: 20.59,  lng: 78.96  },
  'BBC Portuguese': { region: 'South America',  code: 'pt', lat: -14.24, lng: -51.93 },
  'BBC Russian':    { region: 'Eastern Europe', code: 'ru', lat: 55.75,  lng: 37.62  },
  'BBC Japanese':   { region: 'East Asia',      code: 'ja', lat: 36.20,  lng: 138.25 },
  'BBC Swahili':    { region: 'East Africa',    code: 'sw', lat: -1.29,  lng: 36.82  },
};

/** Source name to chart color */
export const SOURCE_COLORS = {
  'BBC Spanish':    '#FF6B6B',
  'BBC Hindi':      '#FFD93D',
  'BBC Portuguese': '#6BCB77',
  'BBC Russian':    '#BC8CFF',
  'BBC Japanese':   '#58A6FF',
  'BBC Swahili':    '#FF8C42',
};

import { iconOverview, iconReport, iconMap, iconSearch } from './icons.js';

/** Navigation items for the sidebar */
export const NAV_ITEMS = [
  { label: 'Overview', hash: 'overview', icon: iconOverview(20) },
  { label: 'Intelligence Reports', hash: 'reports', icon: iconReport(20) },
  { label: 'Global Heatmap', hash: 'heatmap', icon: iconMap(20) },
  { label: 'Entity Explorer', hash: 'entities', icon: iconSearch(20) },
];

/** Entity label to style class */
export const ENTITY_STYLES = {
  'PERSON': { className: 'entity-tag--person', color: '#BC8CFF' },
  'ORG':    { className: 'entity-tag--org',    color: '#58A6FF' },
  'GPE':    { className: 'entity-tag--gpe',    color: '#3FB950' },
  'NORP':   { className: 'entity-tag--other',  color: '#FFD93D' },
  'DATE':   { className: 'entity-tag--other',  color: '#8b919d' },
  'CARDINAL':{ className: 'entity-tag--other', color: '#8b919d' },
};
