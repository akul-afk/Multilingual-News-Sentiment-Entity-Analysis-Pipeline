import { iconOverview, iconSentiment, iconSearch, iconReport, iconMap } from './icons.js';

/** Design tokens — mirrors the CSS custom properties */
export const COLORS = {
  bg: '#10141a',
  surface: '#1c2026',
  surfaceLow: '#181c22',
  surfaceHigh: '#262a31',
  surfaceHighest: '#31353c',
  surfaceLowest: '#0a0e14',
  primary: '#58A6FF',
  primaryLight: '#a2c9ff',
  secondary: '#BC8CFF',
  tertiary: '#3FB950',
  error: '#f85149',
  text: '#dfe2eb',
  textMuted: '#c0c7d4',
  textDim: '#8b919d',
  outline: '#414752',
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

/** Entity label to style class */
export const ENTITY_STYLES = {
  'PERSON': { className: 'entity-tag--person', color: '#BC8CFF' },
  'ORG':    { className: 'entity-tag--org',    color: '#58A6FF' },
  'GPE':    { className: 'entity-tag--gpe',    color: '#3FB950' },
  'NORP':   { className: 'entity-tag--other',  color: '#FFD93D' },
  'DATE':   { className: 'entity-tag--other',  color: '#8b919d' },
  'CARDINAL':{ className: 'entity-tag--other', color: '#8b919d' },
};

/** Navigation items — icons are SVG strings */
export const NAV_ITEMS = [
  { id: 'overview',  icon: iconOverview(18),  label: 'Overview',           hash: '#overview' },
  { id: 'sentiment', icon: iconSentiment(18), label: 'Sentiment Analysis', hash: '#sentiment' },
  { id: 'entities',  icon: iconSearch(18),    label: 'Entity Explorer',    hash: '#entities' },
  { id: 'reports',   icon: iconReport(18),    label: 'Reports',            hash: '#reports' },
  { id: 'heatmap',   icon: iconMap(18),       label: 'Geo Heatmap',        hash: '#heatmap' },
];
