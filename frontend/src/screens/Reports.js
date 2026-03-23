import Chart from 'chart.js/auto';
import { COLORS, SOURCE_COLORS } from '../utils/constants.js';
import { iconClipboard, iconTrendUp, iconTrendDown, iconBarChart, iconChevronDown, iconGlobe, iconPieChart } from '../utils/icons.js';
import { formatPolarity, sentimentLabel, formatDate, formatDayName, pct } from '../utils/formatters.js';

export function renderReports(container, data) {
  const weekly = data.weekly_reports || [];
  const monthly = data.monthly_reports || [];

  let activeTab = 'weekly';
  let reports = weekly;
  let selectedIdx = reports.length - 1;

  const el = document.createElement('div');

  function render() {
    reports = activeTab === 'weekly' ? weekly : monthly;
    selectedIdx = Math.min(selectedIdx, reports.length - 1);
    if (selectedIdx < 0) selectedIdx = 0;
    const report = reports[selectedIdx] || {};
    const dist = report.sentiment_distribution || {};
    const total = (dist.positive || 0) + (dist.neutral || 0) + (dist.negative || 0);

    // Clean takeaways (remove emojis from backend data)
    const takeaways = (report.key_takeaways || []).map(t =>
      t.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '').trim()
    );

    el.innerHTML = `
      <div class="page-title" style="display: flex; align-items: center; justify-content: space-between">
        <div>
          <h1>Intelligence Reports</h1>
          <p>Automated weekly and monthly trend summaries from global news sources</p>
        </div>
        <div style="display: flex; gap: var(--space-4); align-items: center">
          <div class="pills">
            <button class="pill ${activeTab === 'weekly' ? 'pill--active' : ''}" id="tab-weekly">Weekly Report</button>
            <button class="pill ${activeTab === 'monthly' ? 'pill--active' : ''}" id="tab-monthly">Monthly Report</button>
          </div>
          <select id="period-select" style="background: var(--surface-lowest); color: var(--text); border: 1px solid var(--glass-border); padding: var(--space-2) var(--space-4); border-radius: var(--radius-md); font-family: var(--font-body); font-size: 0.85rem">
            ${reports.map((r, i) => `<option value="${i}" ${i === selectedIdx ? 'selected' : ''}>${r.label} (${r.period_start})</option>`).join('')}
          </select>
        </div>
      </div>

      <!-- Executive Summary -->
      <div class="card card--glass" style="margin-bottom: var(--space-6); border-left: 3px solid var(--primary)">
        <div class="card__header">
          <span class="card__title" style="display: flex; align-items: center; gap: 8px">
            ${iconClipboard(16, COLORS.primary)}
            ${activeTab === 'weekly' ? 'Weekly' : 'Monthly'} Executive Summary
          </span>
        </div>
        <div style="display: flex; gap: var(--space-3); margin-bottom: var(--space-4); flex-wrap: wrap">
          ${takeaways.map(t => `<span class="badge badge--primary">${t}</span>`).join('')}
        </div>
        <p style="color: var(--text-muted); line-height: 1.7; font-size: 0.9rem">${report.summary || 'No data available.'}</p>
      </div>

      <div class="grid grid--65-35">
        <div>
          <!-- Sentiment Shift Chart -->
          <div class="card" style="margin-bottom: var(--space-6)">
            <div class="card__header">
              <span class="card__title">Sentiment Shift by Source</span>
            </div>
            <div class="chart-wrapper" style="height: 250px">
              <canvas id="shift-chart"></canvas>
            </div>
          </div>

          <!-- Top Stories -->
          <div class="card" style="margin-bottom: var(--space-6)">
            <div class="card__header">
              <span class="card__title">Top Stories This Period</span>
              <span class="text-dim" style="font-size: 0.8rem">${(report.top_stories || []).length} stories</span>
            </div>
            ${(report.top_stories || []).map((story, i) => `
              <div style="display: flex; gap: var(--space-3); padding: var(--space-3) 0; ${i < (report.top_stories || []).length - 1 ? 'border-bottom: 1px solid rgba(65,71,82,0.1)' : ''}">
                <span style="font-weight: 800; color: var(--primary); font-size: 1.1rem; min-width: 24px">${i + 1}</span>
                <div style="flex: 1">
                  <div style="font-size: 0.85rem; margin-bottom: 4px">${story.Translated_Headline || ''}</div>
                  <div style="display: flex; gap: var(--space-2)">
                    <span class="badge badge--primary">${(story.Source_Name || '').replace('BBC ', '')}</span>
                    <span class="badge badge--${sentimentLabel(story.Polarity).toLowerCase()}">${formatPolarity(story.Polarity)}</span>
                  </div>
                </div>
              </div>
            `).join('')}
          </div>

          <!-- Daily Archive -->
          <div class="card">
            <div class="card__header">
              <span class="card__title">Detailed News Archive — ${report.label || ''}</span>
            </div>
            ${Object.entries(report.daily_breakdown || {}).map(([date, day], i) => `
              <div class="accordion__item">
                <button class="accordion__header" data-idx="${i}">
                  <span>
                    <strong>${formatDayName(date)}</strong>
                    <span class="text-dim" style="margin-left: 8px; font-weight: 400">${formatDate(date)} — ${day.count} Stories</span>
                  </span>
                  <span style="display: flex; align-items: center; gap: 6px">
                    <span class="source-dot" style="background: ${day.avg_polarity >= 0 ? COLORS.tertiary : COLORS.error}; width: 8px; height: 8px; border-radius: 50%"></span>
                    <span style="display:flex">${iconChevronDown(12, COLORS.textDim)}</span>
                  </span>
                </button>
                <div class="accordion__content ${i === 0 ? 'accordion__content--open' : ''}">
                  <div class="accordion__content-inner">
                    <div class="table-container">
                      <table class="table">
                        <thead><tr><th>Source</th><th>Headline</th><th>Sentiment</th></tr></thead>
                        <tbody>
                          ${(day.headlines || []).map(h => `
                            <tr>
                              <td><span class="badge badge--primary">${(h.Source_Name || '').replace('BBC ', '')}</span></td>
                              <td style="max-width: 350px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">${h.Translated_Headline || ''}</td>
                              <td><span class="badge badge--${sentimentLabel(h.Polarity).toLowerCase()}">${formatPolarity(h.Polarity)}</span></td>
                            </tr>
                          `).join('')}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Right Panel -->
        <div>
          <div class="card" style="margin-bottom: var(--space-6)">
            <div class="card__header">
              <span class="card__title" style="display: flex; align-items: center; gap: 8px">
                ${iconBarChart(16, COLORS.primary)}
                Period Statistics
              </span>
            </div>
            <div class="stat-row"><span class="stat-row__label">Total Headlines</span><span class="stat-row__value">${report.total_headlines || 0}</span></div>
            <div class="stat-row"><span class="stat-row__label">Unique Entities</span><span class="stat-row__value">${report.unique_entities || 0}</span></div>
            <div class="stat-row"><span class="stat-row__label">Most Active Source</span><span class="stat-row__value"><span class="badge badge--primary">${(report.most_active_source || '').replace('BBC ', '')}</span></span></div>
            <div class="stat-row"><span class="stat-row__label">Most Positive Source</span><span class="stat-row__value"><span class="badge badge--positive">${(report.most_positive_source || '').replace('BBC ', '')}</span></span></div>
            <div class="stat-row"><span class="stat-row__label">Avg Polarity</span><span class="stat-row__value" style="color: ${(report.avg_polarity || 0) >= 0 ? COLORS.tertiary : COLORS.error}">${formatPolarity(report.avg_polarity || 0)}</span></div>
          </div>

          <div class="card">
            <div class="card__header">
              <span class="card__title">Sentiment Distribution</span>
            </div>
            <div class="chart-wrapper" style="height: 200px">
              <canvas id="dist-donut"></canvas>
            </div>
            <div style="margin-top: var(--space-4)">
              <div class="stat-row"><span class="stat-row__label"><span style="color: var(--tertiary)">●</span> Positive</span><span class="stat-row__value">${pct(dist.positive, total)}</span></div>
              <div class="stat-row"><span class="stat-row__label"><span style="color: var(--text-dim)">●</span> Neutral</span><span class="stat-row__value">${pct(dist.neutral, total)}</span></div>
              <div class="stat-row"><span class="stat-row__label"><span style="color: var(--error)">●</span> Negative</span><span class="stat-row__value">${pct(dist.negative, total)}</span></div>
            </div>
          </div>
        </div>
      </div>
    `;

    container.innerHTML = '';
    container.appendChild(el);
    bindEvents();
    renderCharts(report);
  }

  function bindEvents() {
    document.getElementById('tab-weekly')?.addEventListener('click', () => { activeTab = 'weekly'; selectedIdx = weekly.length - 1; render(); });
    document.getElementById('tab-monthly')?.addEventListener('click', () => { activeTab = 'monthly'; selectedIdx = monthly.length - 1; render(); });
    document.getElementById('period-select')?.addEventListener('change', (e) => { selectedIdx = parseInt(e.target.value); render(); });

    el.querySelectorAll('.accordion__header').forEach(header => {
      header.addEventListener('click', () => {
        const content = header.nextElementSibling;
        content.classList.toggle('accordion__content--open');
      });
    });
  }

  function renderCharts(report) {
    const sources = Object.keys(report.source_sentiment || {});
    const curr = sources.map(s => report.source_sentiment[s]);
    const prev = sources.map(s => report.prev_source_sentiment?.[s] ?? null);

    const shiftCanvas = document.getElementById('shift-chart');
    if (shiftCanvas && sources.length) {
      new Chart(shiftCanvas, {
        type: 'bar',
        data: {
          labels: sources.map(s => s.replace('BBC ', '')),
          datasets: [
            { label: 'This Period', data: curr, backgroundColor: COLORS.primary, borderRadius: 4, barPercentage: 0.6 },
            { label: 'Previous Period', data: prev, backgroundColor: COLORS.surfaceHighest, borderRadius: 4, barPercentage: 0.6 },
          ],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom', labels: { color: COLORS.textMuted, usePointStyle: true } } },
          scales: {
            x: { grid: { display: false }, ticks: { color: COLORS.textMuted } },
            y: { grid: { color: 'rgba(65,71,82,0.15)' }, ticks: { color: COLORS.textDim } },
          },
        },
      });
    }

    const distCanvas = document.getElementById('dist-donut');
    const dist = report.sentiment_distribution || {};
    if (distCanvas) {
      new Chart(distCanvas, {
        type: 'doughnut',
        data: {
          labels: ['Positive', 'Neutral', 'Negative'],
          datasets: [{ data: [dist.positive || 0, dist.neutral || 0, dist.negative || 0], backgroundColor: [COLORS.tertiary, COLORS.textDim, COLORS.error], borderWidth: 0 }],
        },
        options: {
          responsive: true, maintainAspectRatio: false, cutout: '65%',
          plugins: { legend: { display: false } },
        },
      });
    }
  }

  render();
}
