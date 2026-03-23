import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import { COLORS, SOURCE_COLORS } from '../utils/constants.js';
import { iconFlag, iconLive, iconActivity } from '../utils/icons.js';
import { formatPolarity, sentimentLabel, pct } from '../utils/formatters.js';

export function renderHeatmap(container, data) {
  const geo = data.geo_data || [];
  const selectedRegion = geo[0] || {};

  const el = document.createElement('div');
  el.innerHTML = `
    <div class="page-title" style="display: flex; align-items: center; justify-content: space-between">
      <div>
        <h1>Global News Heatmap</h1>
        <p>Geographic distribution of news activity by source region</p>
      </div>
      <div style="display: flex; align-items: center; gap: var(--space-3)">
        <span class="text-dim" style="font-size: 0.75rem">COLD</span>
        <div style="width: 100px; height: 8px; border-radius: 4px; background: linear-gradient(to right, #1a4580, #58A6FF, #FFD93D, #FF6B6B, #f85149)"></div>
        <span class="text-dim" style="font-size: 0.75rem">HOT</span>
      </div>
    </div>

    <div class="grid grid--70-30">
      <div>
        <!-- Map Container -->
        <div class="card" style="padding: 0; margin-bottom: var(--space-6); overflow: hidden">
          <div id="news-map" class="map-container"></div>
        </div>

        <!-- Region Stats Bar -->
        <div class="grid grid--3" style="gap: var(--space-3)">
          ${geo.map(g => {
            const dist = g.sentiment || {};
            const total = (dist.positive || 0) + (dist.neutral || 0) + (dist.negative || 0);
            const posPct = total ? (dist.positive || 0) / total * 100 : 0;
            const neuPct = total ? (dist.neutral || 0) / total * 100 : 0;
            const negPct = total ? (dist.negative || 0) / total * 100 : 0;
            return `
              <div class="card" style="padding: var(--space-4)">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-2)">
                  <span style="font-weight: 600; font-size: 0.85rem; display: flex; align-items: center; gap: 6px">
                    ${iconFlag(g.lang_code, 18)}
                    ${g.region}
                  </span>
                  <span class="badge badge--primary" style="font-size: 0.7rem">${g.source_name?.replace('BBC ', '') || ''}</span>
                </div>
                <div style="font-family: var(--font-heading); font-weight: 800; font-size: 1.5rem; color: ${g.avg_polarity >= 0 ? COLORS.tertiary : COLORS.error}">${g.total_headlines}</div>
                <div style="font-size: 0.75rem; color: var(--text-dim); margin-bottom: var(--space-2)">headlines</div>
                <div style="display: flex; height: 4px; border-radius: 2px; overflow: hidden; gap: 1px">
                  <div style="width: ${posPct}%; background: ${COLORS.tertiary}"></div>
                  <div style="width: ${neuPct}%; background: ${COLORS.textDim}"></div>
                  <div style="width: ${negPct}%; background: ${COLORS.error}"></div>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>

      <!-- Hotspot Details Panel -->
      <div>
        <div class="card" style="margin-bottom: var(--space-6)">
          <div class="card__header">
            <span class="card__title">Hotspot Details</span>
            <span class="badge badge--positive" style="display: flex; align-items: center; gap: 4px">${iconLive(8)} LIVE</span>
          </div>
          <h3 style="font-size: 1.1rem; margin-bottom: var(--space-2)">${selectedRegion.region || 'N/A'}</h3>
          <p class="text-dim" style="font-size: 0.8rem; margin-bottom: var(--space-4)">${selectedRegion.source_name || ''}</p>

          <div class="grid grid--2" style="gap: var(--space-3); margin-bottom: var(--space-5)">
            <div style="text-align: center; padding: var(--space-3); background: var(--surface-low); border-radius: var(--radius-md)">
              <div style="font-size: 0.7rem; color: var(--text-dim)">NEWS VOLUME</div>
              <div style="font-family: var(--font-heading); font-weight: 800; font-size: 1.4rem; color: var(--primary)">${selectedRegion.total_headlines || 0}</div>
            </div>
            <div style="text-align: center; padding: var(--space-3); background: var(--surface-low); border-radius: var(--radius-md)">
              <div style="font-size: 0.7rem; color: var(--text-dim)">AVG POLARITY</div>
              <div style="font-family: var(--font-heading); font-weight: 800; font-size: 1.4rem; color: ${(selectedRegion.avg_polarity || 0) >= 0 ? COLORS.tertiary : COLORS.error}">${formatPolarity(selectedRegion.avg_polarity || 0)}</div>
            </div>
          </div>

          <h4 style="font-size: 0.8rem; color: var(--text-dim); margin-bottom: var(--space-2)">SENTIMENT ANALYSIS</h4>
          ${(() => {
            const d = selectedRegion.sentiment || {};
            const t = (d.positive || 0) + (d.neutral || 0) + (d.negative || 0);
            return `
              <div style="display: flex; height: 12px; border-radius: 6px; overflow: hidden; gap: 2px; margin-bottom: var(--space-4)">
                <div style="width: ${t ? d.positive / t * 100 : 0}%; background: ${COLORS.tertiary}; border-radius: 4px"></div>
                <div style="width: ${t ? d.neutral / t * 100 : 0}%; background: ${COLORS.textDim}; border-radius: 4px"></div>
                <div style="width: ${t ? d.negative / t * 100 : 0}%; background: ${COLORS.error}; border-radius: 4px"></div>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-dim)">
                <span style="color: ${COLORS.tertiary}">POS ${pct(d.positive, t)}</span>
                <span>NEU ${pct(d.neutral, t)}</span>
                <span style="color: ${COLORS.error}">NEG ${pct(d.negative, t)}</span>
              </div>
            `;
          })()}

          <h4 style="font-size: 0.8rem; color: var(--text-dim); margin-top: var(--space-5); margin-bottom: var(--space-3)">7-DAY ACTIVITY</h4>
          <div style="display: flex; align-items: flex-end; gap: 3px; height: 50px">
            ${(selectedRegion.activity_timeline || []).map(day => {
              const maxCount = Math.max(...(selectedRegion.activity_timeline || []).map(d => d.count), 1);
              const height = Math.max(4, (day.count / maxCount) * 46);
              return `<div style="flex: 1; height: ${height}px; background: var(--primary); border-radius: 2px; opacity: 0.7" title="${day.date}: ${day.count}"></div>`;
            }).join('')}
          </div>
        </div>
      </div>
    </div>
  `;

  container.appendChild(el);

  // ── Initialize Leaflet Map ──
  setTimeout(() => {
    const mapEl = document.getElementById('news-map');
    if (!mapEl) return;

    const map = L.map('news-map', {
      center: [20, 30],
      zoom: 2,
      minZoom: 2,
      maxZoom: 6,
      zoomControl: true,
      attributionControl: false,
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map);

    const heatPoints = geo.map(g => [g.lat, g.lng, g.intensity * 50]);
    if (heatPoints.length) {
      L.heatLayer(heatPoints, {
        radius: 50,
        blur: 30,
        maxZoom: 5,
        gradient: { 0.2: '#1a4580', 0.4: '#58A6FF', 0.6: '#FFD93D', 0.8: '#FF6B6B', 1.0: '#f85149' },
      }).addTo(map);
    }

    geo.forEach(g => {
      const circle = L.circleMarker([g.lat, g.lng], {
        radius: Math.max(8, Math.sqrt(g.total_headlines) * 2),
        color: SOURCE_COLORS[g.source_name] || COLORS.primary,
        fillColor: SOURCE_COLORS[g.source_name] || COLORS.primary,
        fillOpacity: 0.3,
        weight: 2,
      }).addTo(map);

      circle.bindTooltip(`
        <div class="map-tooltip">
          <div class="tooltip-title">${g.region}</div>
          <div class="tooltip-stat">${g.total_headlines} headlines | Avg: ${formatPolarity(g.avg_polarity)}</div>
        </div>
      `, { className: 'map-tooltip', direction: 'top', offset: [0, -10] });
    });
  }, 100);
}
