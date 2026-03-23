import Chart from 'chart.js/auto';
import { COLORS, SOURCE_COLORS } from '../utils/constants.js';
import { iconNewspaper, iconTarget, iconRadio, iconScan, iconTag, iconArrowUp, iconArrowDown, iconFlag } from '../utils/icons.js';
import { formatPolarity, formatDate, compactNumber, sentimentLabel, pct } from '../utils/formatters.js';

export function renderOverview(container, data) {
  const daily = data.daily_summary || [];
  const entities = data.entities?.entities || [];
  const geo = data.geo_data || [];
  const recent = data.recent_headlines || [];

  // Latest day stats
  const latestDay = daily[daily.length - 1] || {};
  const prevDay = daily[daily.length - 2] || {};
  const totalToday = latestDay.total_headlines || 0;
  const totalYesterday = prevDay.total_headlines || 0;
  const avgPol = latestDay.avg_polarity || 0;
  const sourcesActive = Object.keys(latestDay.sources || {}).length;

  const el = document.createElement('div');
  el.innerHTML = `
    <div class="page-title">
      <h1>Dashboard Overview</h1>
      <p>Real-time insights from multilingual news analysis across 6 BBC language services</p>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid--4" style="margin-bottom: var(--space-6)">
      <div class="card kpi">
        <div class="card__header"><span class="card__title">Headlines Today</span><span class="card__icon">${iconNewspaper(18, COLORS.textDim)}</span></div>
        <div class="kpi__value">${compactNumber(totalToday)}</div>
        <span class="kpi__change ${totalToday >= totalYesterday ? 'kpi__change--up' : 'kpi__change--down'}">
          ${totalToday >= totalYesterday ? iconArrowUp(12) : iconArrowDown(12)} ${Math.abs(totalToday - totalYesterday)} vs yesterday
        </span>
      </div>
      <div class="card kpi">
        <div class="card__header"><span class="card__title">Avg Sentiment</span><span class="card__icon">${iconTarget(18, COLORS.textDim)}</span></div>
        <div class="kpi__value" style="color: ${avgPol >= 0 ? COLORS.tertiary : COLORS.error}">${formatPolarity(avgPol)}</div>
        <span class="kpi__change ${avgPol >= 0 ? 'kpi__change--up' : 'kpi__change--down'}">
          ${sentimentLabel(avgPol)}
        </span>
      </div>
      <div class="card kpi">
        <div class="card__header"><span class="card__title">Active Sources</span><span class="card__icon">${iconRadio(18, COLORS.textDim)}</span></div>
        <div class="kpi__value">${sourcesActive}</div>
        <span class="kpi__change kpi__change--up">All services reporting</span>
      </div>
      <div class="card kpi">
        <div class="card__header"><span class="card__title">Entities Detected</span><span class="card__icon">${iconScan(18, COLORS.textDim)}</span></div>
        <div class="kpi__value">${compactNumber(data.total_entities || 0)}</div>
        <span class="kpi__change kpi__change--up">${entities.length} unique</span>
      </div>
    </div>

    <!-- Main content -->
    <div class="grid grid--65-35">
      <div>
        <!-- Sentiment Trend Chart -->
        <div class="card" style="margin-bottom: var(--space-6)">
          <div class="card__header">
            <span class="card__title">Sentiment Trend Over Time</span>
            <span class="text-dim" style="font-size: 0.8rem">Last 30 days</span>
          </div>
          <div class="chart-wrapper" style="height: 300px">
            <canvas id="trend-chart"></canvas>
          </div>
        </div>

        <!-- Recent Headlines -->
        <div class="card">
          <div class="card__header">
            <span class="card__title">Recent Headlines</span>
            <span class="text-dim" style="font-size: 0.8rem">${recent.length} headlines</span>
          </div>
          <div class="table-container" style="max-height: 320px; overflow-y: auto">
            <table class="table">
              <thead><tr><th>Source</th><th>Headline</th><th>Sentiment</th></tr></thead>
              <tbody>
                ${recent.slice(0, 15).map(h => `
                  <tr>
                    <td><span class="badge badge--primary">${h.Source_Name?.replace('BBC ', '') || 'N/A'}</span></td>
                    <td style="max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">${h.Translated_Headline || ''}</td>
                    <td><span class="badge badge--${sentimentLabel(h.Polarity).toLowerCase()}">${sentimentLabel(h.Polarity)} ${formatPolarity(h.Polarity)}</span></td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div>
        <!-- Top Entities -->
        <div class="card" style="margin-bottom: var(--space-6)">
          <div class="card__header">
            <span class="card__title">Top Entities</span>
            <span class="card__icon">${iconTag(18, COLORS.textDim)}</span>
          </div>
          <div class="chart-wrapper" style="height: 300px">
            <canvas id="entities-chart"></canvas>
          </div>
        </div>

        <!-- Source Health -->
        <div class="card">
          <div class="card__header">
            <span class="card__title">Source Health</span>
          </div>
          ${geo.map(g => `
            <div class="stat-row">
              <span class="stat-row__label" style="display: flex; align-items: center; gap: 6px">
                <span class="source-dot source-dot--active"></span>
                <span style="display:inline-flex">${iconFlag(g.lang_code, 16)}</span>
                ${g.source_name?.replace('BBC ', '') || ''}
              </span>
              <span class="stat-row__value">${g.total_headlines} headlines
                <span style="color: ${g.avg_polarity >= 0 ? COLORS.tertiary : COLORS.error}; margin-left: 6px; font-size: 0.8rem">${formatPolarity(g.avg_polarity)}</span>
              </span>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;

  container.appendChild(el);

  // ── Render Sentiment Trend Chart ──
  const last30 = daily.slice(-30);
  const dates = last30.map(d => formatDate(d.date));
  const sources = [...new Set(last30.flatMap(d => Object.keys(d.sources || {})))];

  const datasets = sources.map(src => ({
    label: src.replace('BBC ', ''),
    data: last30.map(d => d.sources?.[src]?.avg_polarity ?? null),
    borderColor: SOURCE_COLORS[src] || COLORS.primary,
    backgroundColor: 'transparent',
    borderWidth: 2,
    tension: 0.4,
    pointRadius: 0,
    pointHoverRadius: 4,
  }));

  new Chart(document.getElementById('trend-chart'), {
    type: 'line',
    data: { labels: dates, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: COLORS.textMuted, padding: 16, usePointStyle: true, pointStyle: 'circle' } },
      },
      scales: {
        x: { grid: { color: 'rgba(65,71,82,0.15)' }, ticks: { color: COLORS.textDim, maxTicksLimit: 8 } },
        y: { grid: { color: 'rgba(65,71,82,0.15)' }, ticks: { color: COLORS.textDim }, suggestedMin: -0.5, suggestedMax: 0.5 },
      },
      interaction: { intersect: false, mode: 'index' },
    },
  });

  // ── Render Top Entities Chart ──
  const topEntities = entities.slice(0, 10);
  new Chart(document.getElementById('entities-chart'), {
    type: 'bar',
    data: {
      labels: topEntities.map(e => e.name),
      datasets: [{
        data: topEntities.map(e => e.count),
        backgroundColor: topEntities.map(e => {
          const style = { 'PERSON': COLORS.secondary, 'ORG': COLORS.primary, 'GPE': COLORS.tertiary };
          return style[e.label] || COLORS.textDim;
        }),
        borderRadius: 4,
        barThickness: 18,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: 'rgba(65,71,82,0.15)' }, ticks: { color: COLORS.textDim } },
        y: { grid: { display: false }, ticks: { color: COLORS.textMuted, font: { size: 11 } } },
      },
    },
  });
}
