import Chart from 'chart.js/auto';
import { COLORS, SOURCE_COLORS } from '../utils/constants.js';
import { formatPolarity, sentimentLabel, formatDate, pct } from '../utils/formatters.js';

export function renderSentiment(container, data) {
  const daily = data.daily_summary || [];
  const recent = data.recent_headlines || [];
  const sources = Object.keys(SOURCE_COLORS);

  const el = document.createElement('div');
  el.innerHTML = `
    <div class="page-title">
      <h1>Sentiment Analysis</h1>
      <p>Deep-dive into sentiment distribution across all news sources</p>
    </div>

    <!-- Stacked Area Chart -->
    <div class="card" style="margin-bottom: var(--space-6)">
      <div class="card__header">
        <span class="card__title">Sentiment Distribution Over Time</span>
      </div>
      <div class="chart-wrapper" style="height: 300px">
        <canvas id="sentiment-area-chart"></canvas>
      </div>
    </div>

    <!-- Source Comparison Grid -->
    <div class="grid grid--3" style="margin-bottom: var(--space-6)">
      ${sources.map(src => {
        const srcDays = daily.filter(d => d.sources?.[src]);
        const avgPol = srcDays.length ? srcDays.reduce((s, d) => s + (d.sources[src]?.avg_polarity || 0), 0) / srcDays.length : 0;
        const totalCount = srcDays.reduce((s, d) => s + (d.sources[src]?.count || 0), 0);
        return `
          <div class="card">
            <div class="card__header">
              <span class="card__title">${src}</span>
              <span class="badge badge--primary">${totalCount} headlines</span>
            </div>
            <div style="display: flex; align-items: center; gap: var(--space-4)">
              <div class="gauge-container">
                <canvas id="gauge-${src.replace(/\s/g, '-')}" width="120" height="120"></canvas>
                <div class="gauge__center-value" style="color: ${avgPol >= 0 ? COLORS.tertiary : COLORS.error}">${formatPolarity(avgPol)}</div>
              </div>
              <div style="flex: 1">
                <div class="stat-row">
                  <span class="stat-row__label">Avg Polarity</span>
                  <span class="stat-row__value" style="color: ${avgPol >= 0 ? COLORS.tertiary : COLORS.error}">${formatPolarity(avgPol)}</span>
                </div>
                <div class="stat-row">
                  <span class="stat-row__label">Headlines</span>
                  <span class="stat-row__value">${totalCount}</span>
                </div>
                <div class="sparkline-container">
                  <canvas id="spark-${src.replace(/\s/g, '-')}"></canvas>
                </div>
              </div>
            </div>
          </div>
        `;
      }).join('')}
    </div>

    <!-- Headlines Table -->
    <div class="card">
      <div class="card__header">
        <span class="card__title">Recent Multilingual Headlines</span>
      </div>
      <div class="table-container" style="max-height: 400px; overflow-y: auto">
        <table class="table">
          <thead><tr><th>Source</th><th>Original</th><th>Translated</th><th>Sentiment</th><th>Polarity</th></tr></thead>
          <tbody>
            ${recent.slice(0, 25).map(h => `
              <tr>
                <td><span class="badge badge--primary">${h.Source_Name?.replace('BBC ', '') || ''}</span></td>
                <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.8rem; color: var(--text-dim)">${h.Original_Headline || ''}</td>
                <td style="max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">${h.Translated_Headline || ''}</td>
                <td><span class="badge badge--${sentimentLabel(h.Polarity).toLowerCase()}">${sentimentLabel(h.Polarity)}</span></td>
                <td style="color: ${h.Polarity >= 0 ? COLORS.tertiary : COLORS.error}; font-weight: 600">${formatPolarity(h.Polarity)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;

  container.appendChild(el);

  // ── Stacked Area Chart ──
  const last30 = daily.slice(-30);
  const dates = last30.map(d => formatDate(d.date));

  // Calculate positive/neutral/negative counts per day (approximate from polarity)
  const posData = [], neuData = [], negData = [];
  last30.forEach(d => {
    let pos = 0, neu = 0, neg = 0;
    Object.values(d.sources || {}).forEach(s => {
      if (s.avg_polarity > 0.05) pos += s.count;
      else if (s.avg_polarity < -0.05) neg += s.count;
      else neu += s.count;
    });
    posData.push(pos);
    neuData.push(neu);
    negData.push(neg);
  });

  new Chart(document.getElementById('sentiment-area-chart'), {
    type: 'line',
    data: {
      labels: dates,
      datasets: [
        { label: 'Positive', data: posData, backgroundColor: 'rgba(63,185,80,0.3)', borderColor: COLORS.tertiary, fill: true, tension: 0.4, pointRadius: 0 },
        { label: 'Neutral', data: neuData, backgroundColor: 'rgba(139,145,157,0.2)', borderColor: COLORS.textDim, fill: true, tension: 0.4, pointRadius: 0 },
        { label: 'Negative', data: negData, backgroundColor: 'rgba(248,81,73,0.2)', borderColor: COLORS.error, fill: true, tension: 0.4, pointRadius: 0 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { color: COLORS.textMuted, usePointStyle: true } } },
      scales: {
        x: { grid: { color: 'rgba(65,71,82,0.15)' }, ticks: { color: COLORS.textDim, maxTicksLimit: 8 }, stacked: true },
        y: { grid: { color: 'rgba(65,71,82,0.15)' }, ticks: { color: COLORS.textDim }, stacked: true },
      },
    },
  });

  // ── Gauge Charts ──
  sources.forEach(src => {
    const canvasEl = document.getElementById(`gauge-${src.replace(/\s/g, '-')}`);
    if (!canvasEl) return;
    const srcDays = daily.filter(d => d.sources?.[src]);
    const avgPol = srcDays.length ? srcDays.reduce((s, d) => s + (d.sources[src]?.avg_polarity || 0), 0) / srcDays.length : 0;
    const normalized = (avgPol + 1) / 2; // -1..1 → 0..1

    new Chart(canvasEl, {
      type: 'doughnut',
      data: {
        datasets: [{
          data: [normalized, 1 - normalized],
          backgroundColor: [avgPol >= 0 ? COLORS.tertiary : COLORS.error, COLORS.surfaceHigh],
          borderWidth: 0,
          circumference: 270,
          rotation: 225,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: true, cutout: '75%',
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
      },
    });
  });

  // ── Sparklines ──
  sources.forEach(src => {
    const canvasEl = document.getElementById(`spark-${src.replace(/\s/g, '-')}`);
    if (!canvasEl) return;
    const srcDays = daily.slice(-14).filter(d => d.sources?.[src]);
    new Chart(canvasEl, {
      type: 'line',
      data: {
        labels: srcDays.map((_, i) => i),
        datasets: [{
          data: srcDays.map(d => d.sources[src]?.avg_polarity || 0),
          borderColor: SOURCE_COLORS[src] || COLORS.primary,
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.4,
          fill: false,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        scales: { x: { display: false }, y: { display: false } },
      },
    });
  });
}
