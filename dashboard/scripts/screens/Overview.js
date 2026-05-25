import { registerChart } from '../utils/chartManager.js';
import { iconArrowUp, iconArrowDown, iconTrendUp, iconTrendDown } from '../icons.js';

const crosshairPlugin = {
  id: 'crosshair',
  afterDraw(chart) {
    if (chart.tooltip?._active?.length) {
      const ctx = chart.ctx;
      const x = chart.tooltip._active[0].element.x;
      const top = chart.chartArea.top;
      const bottom = chart.chartArea.bottom;
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(x, top);
      ctx.lineTo(x, bottom);
      ctx.lineWidth = 1;
      ctx.strokeStyle = 'rgba(139,0,0,0.3)';
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.restore();
    }
  }
};

Chart.register(crosshairPlugin);

function rollingAverage(data, windowSize) {
  return data.map((d, i) => {
    if (d.y === null) {
      return { x: d.x, y: null };
    }
    const slice = data.slice(Math.max(0, i - windowSize + 1), i + 1)
      .filter(p => p.y !== null);
    if (slice.length === 0) {
      return { x: d.x, y: null };
    }
    const avg = slice.reduce((s, p) => s + p.y, 0) / slice.length;
    return { x: d.x, y: parseFloat(avg.toFixed(4)) };
  });
}

export function mountOverview(container, data) {
    // Note: weekly_reports is sorted ascending (oldest first).
    // The latest week is at the end of the array.
    const wr = data.weekly_reports || [];
    const latestReport = wr.length > 0 ? wr[wr.length - 1] : {};
    const prevReport = wr.length > 1 ? wr[wr.length - 2] : {};

    // Resolve `--positive` green variable from CSS context dynamically
    const positiveColor = getComputedStyle(document.documentElement).getPropertyValue('--positive').trim() || '#1b4d3e';

    // Fix 1 — Chart: use daily_summary for the sentiment series
    const series = (data.daily_summary || [])
      .filter(d => (d.headline_count || d.total_headlines || d.count || 1) >= 5)
      .map(d => ({
        x: d.date ? d.date.replace(/_/g, '-') : null,
        y: d.avg_polarity ?? d.average_polarity ?? d.polarity ?? null
      }))
      .filter(d => d.x && d.y !== null)
      .sort((a, b) => a.x.localeCompare(b.x));

    const chartData = [];
    
    if (series.length > 0) {
        // Parse ISO date string (YYYY-MM-DD) to Date object
        const parseDateStr = (str) => {
            const parts = str.split('-');
            return new Date(parts[0], parts[1] - 1, parts[2]);
        };
        
        // Format Date object to YYYY-MM-DD string
        const formatDateStr = (date) => {
            const y = date.getFullYear();
            const m = String(date.getMonth() + 1).padStart(2, '0');
            const d = String(date.getDate()).padStart(2, '0');
            return `${y}-${m}-${d}`;
        };
        
        // Map YYYY-MM-DD to polarity
        const trendMap = {};
        series.forEach(d => {
            trendMap[d.x] = d.y;
        });
        
        // Generate continuous daily timeline
        const start = parseDateStr(series[0].x);
        const end = parseDateStr(series[series.length - 1].x);
        
        let current = new Date(start);
        while (current <= end) {
            const key = formatDateStr(current);
            const val = trendMap[key] !== undefined ? trendMap[key] : null;
            
            // Pass objects with x (ISO date string) and y (polarity/null)
            chartData.push({ x: key, y: val });
            
            current.setDate(current.getDate() + 1);
        }
    }

    // Fix 2 — Headlines: use recent_headlines with correct casing
    const raw = data.recent_headlines || [];

    const HEADLINE_NOISE = [
      'rooney', 'recipe', 'heart attack', 'diet', 'fitness',
      'cricket score', 'match preview', 'vikramshila', 'bridge',
      'royal kitchen', 'dishes', 'bollywood', 'box office'
    ];

    const topEntities = (data.entities?.entities || [])
      .map(e => (e.text || e.name || '').toLowerCase());

    const filtered = raw.filter(h => {
      const text = (h.Translated_Headline || '').toLowerCase();
      const polarity = Math.abs(h.Polarity || 0);
      const isNoise = HEADLINE_NOISE.some(n => text.includes(n));
      const hasEntity = topEntities.some(e => e && text.includes(e));
      return !isNoise && (polarity > 0.1 || hasEntity);
    });

    const seen = new Set();
    const deduped = filtered.filter(h => {
      const key = (h.Translated_Headline || '').toLowerCase()
        .replace(/[^a-z0-9\s]/g, '').substring(0, 60);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    const final = deduped
      .sort((a, b) => Math.abs(b.Polarity) - Math.abs(a.Polarity))
      .slice(0, 6);

    const sortedHeadlines = final;

    // Fix 3 — KPI polarity card: use daily_summary for week comparison
    const summaries = (data.daily_summary || [])
      .sort((a, b) => a.date.localeCompare(b.date));

    const thisWeek = summaries.slice(-7);
    const lastWeek = summaries.slice(-14, -7);

    const avg = arr => arr.reduce((s, d) =>
      s + (d.avg_polarity ?? d.average_polarity ?? 0), 0) / (arr.length || 1);

    const thisWeekAvg = avg(thisWeek);
    const lastWeekAvg = avg(lastWeek);
    const delta = thisWeekAvg - lastWeekAvg;

    const trendLabel = thisWeekAvg > 0.05
      ? (delta > 0 ? '↑ MORE POSITIVE THIS WEEK' : '↓ LESS POSITIVE THIS WEEK')
      : (delta > 0 ? '↑ LESS NEGATIVE THIS WEEK' : '↓ MORE NEGATIVE THIS WEEK');

    const isPositiveTrend = delta > 0;
    const trendText = trendLabel.replace(/[↑↓]\s*/, '');

    const polarityTrendHTML = isPositiveTrend ? `
        <div class="kpi__change kpi__change--up flex items-center gap-1">
            ${iconArrowUp(14)} ${trendText}
        </div>
    ` : `
        <div class="kpi__change kpi__change--down flex items-center gap-1">
            ${iconArrowDown(14)} ${trendText}
        </div>
    `;

    // Mean of all daily_summary entries for overall AVG polarity display
    const allAvgPolarity = summaries.reduce((s, d) => s + (d.avg_polarity ?? d.average_polarity ?? 0), 0) / (summaries.length || 1);

    // KPI Card 3 Entities Added Comparison
    const latestEntities = latestReport.unique_entities || 0;
    const prevEntities = prevReport.unique_entities || 0;
    const newEntitiesCount = latestEntities - prevEntities;
    const isNewEntitiesPositive = newEntitiesCount >= 0;
    
    const entitiesTrendHTML = isNewEntitiesPositive ? `
        <div class="kpi__change kpi__change--up flex items-center gap-1">
            +${newEntitiesCount} NEW THIS WEEK
        </div>
    ` : `
        <div class="kpi__change kpi__change--down flex items-center gap-1">
            ${newEntitiesCount} NEW THIS WEEK
        </div>
    `;

    // Active Source Count & Catalogued Headlines
    let activeSourcesCount = 7; // default fallback
    if (data.sources && Array.isArray(data.sources)) {
        activeSourcesCount = data.sources.length;
    } else if (data.sources_count !== undefined && data.sources_count > 0) {
        activeSourcesCount = data.sources_count;
    } else if (data.reports?.daily?.sources_count) {
        activeSourcesCount = data.reports.daily.sources_count;
    } else {
        // Collect from daily summary
        const uniqueSources = new Set();
        if (Array.isArray(data.daily_summary)) {
            data.daily_summary.forEach(day => {
                if (day.sources) {
                    Object.keys(day.sources).forEach(src => {
                        if (src && src.toLowerCase() !== 'other') {
                            uniqueSources.add(src);
                        }
                    });
                }
            });
        }
        if (uniqueSources.size > 0) {
            activeSourcesCount = uniqueSources.size;
        } else if (latestReport.source_sentiment) {
            activeSourcesCount = Object.keys(latestReport.source_sentiment).length;
        }
    }
    const totalHeadlines = data.total_headlines || latestReport.total_headlines || 4849;

    container.innerHTML = `
        <div class="page-title">
            <p>Global intelligence pipeline — ${activeSourcesCount} active sources — ${totalHeadlines} headlines catalogued</p>
        </div>

        <div class="grid grid--3 mt-8">
            <div class="torn-wrapper">
                <div class="torn-container kpi">
                    <span class="card-category">TOTAL HEADLINES</span>
                    <h3 class="card-title">CATALOGUED SINCE SEP 2025</h3>
                    <div class="kpi__value">${totalHeadlines}</div>
                    <div class="kpi__change kpi__change--up flex items-center gap-1">${iconTrendUp(14)} 12% vs last week</div>
                </div>
            </div>
            <div class="torn-wrapper">
                <div class="torn-container kpi">
                    <span class="card-category">Sentiment Axis</span>
                    <h3 class="card-title">AVG POLARITY</h3>
                    <div class="kpi__value">
                        ${allAvgPolarity > 0 ? '+' : ''}${allAvgPolarity.toFixed(2)}
                    </div>
                    ${polarityTrendHTML}
                </div>
            </div>
            <div class="torn-wrapper">
                <div class="torn-container kpi">
                    <span class="card-category">Entity Network</span>
                    <h3 class="card-title">ACROSS 10+ SOURCES</h3>
                    <div class="kpi__value">${data.total_entities || 0}</div>
                    ${entitiesTrendHTML}
                </div>
            </div>
        </div>

        <div class="grid grid--65-35 mt-8">
            <div class="torn-wrapper">
                <div class="torn-container chart-card">
                    <span class="card-category">Temporal Intelligence</span>
                    <h3 class="card-title">GLOBAL SENTIMENT — 8 MONTH TREND</h3>
                    <div class="chart-area" style="height: 300px;">
                        <canvas id="trendChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="torn-wrapper">
                <div class="torn-container headlines-card">
                    <span class="card-category">SIGNIFICANT DISPATCHES</span>
                    <h3 class="card-title">TOP HEADLINES</h3>
                    <div class="headline-ticker-list" style="max-height: 300px; overflow-y: auto; padding-right: 10px;">
                        <ul class="list-ink">
                            ${sortedHeadlines.map(s => `
                                <li style="margin-bottom: 1rem; border-bottom: 1px dashed var(--outline); padding-bottom: 0.5rem;">
                                    <div style="font-family: var(--font-heading); font-weight: 700; font-size: 0.9rem; text-align: justify;">${s.Translated_Headline || s.translated_headline}</div>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    `;

    const rawSeries = chartData;
    const smoothSeries = rollingAverage(rawSeries, 7);

    const ctx = document.getElementById('trendChart').getContext('2d');
    
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'Daily',
                    data: rawSeries,
                    borderColor: 'rgba(139,0,0,0.25)',
                    borderWidth: 1,
                    pointRadius: 0,
                    tension: 0,
                    spanGaps: false
                },
                {
                    label: '7-day avg',
                    data: smoothSeries,
                    borderColor: '#8b0000',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.3,
                    spanGaps: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: { 
                legend: { display: false },
                tooltip: {
                    enabled: true,
                    backgroundColor: '#1a1008',
                    titleColor: '#c9a96e',
                    bodyColor: '#f4e9d9',
                    borderColor: '#5a3c1e',
                    borderWidth: 1,
                    cornerRadius: 0,
                    titleFont: { family: 'Old Standard TT', size: 13 },
                    bodyFont: { family: 'IBM Plex Serif', size: 12 },
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        title: (items) => {
                            if (!items.length || items[0].parsed.x === undefined) return '';
                            const d = new Date(items[0].parsed.x);
                            return d.toLocaleDateString('en-GB', {
                                day: 'numeric', month: 'long', year: 'numeric'
                            });
                        },
                        label: (item) => {
                            const val = item.parsed.y;
                            if (val === null || val === undefined || isNaN(val)) return null;
                            const tone = val > 0.1 ? 'Positive' : val < -0.1 ? 'Negative' : 'Neutral';
                            return [`Sentiment: ${val.toFixed(3)}`, `Tone: ${tone}`];
                        },
                        afterLabel: (item) => {
                            if (item.datasetIndex !== 0) return '';
                            if (!item.parsed || isNaN(item.parsed.x)) return '';
                            const d = new Date(item.parsed.x);
                            const date = d.toLocaleDateString('sv'); // local YYYY-MM-DD
                            const dateUnderscore = date.replace(/-/g, '_');
                            const entry = (data.daily_summary || []).find(e => e.date === date || e.date === dateUnderscore);
                            if (!entry) return '';
                            const count = entry.headline_count || entry.total_headlines || entry.count || '';
                            return count ? `Headlines: ${count}` : '';
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'month',
                        displayFormats: { month: 'MMM yyyy' }
                    },
                    adapters: { date: {} },
                    ticks: {
                        maxTicksLimit: 8,
                        color: 'var(--outline)',
                        font: { family: 'Inter', size: 10 }
                    },
                    grid: { display: false },
                    border: { color: 'var(--outline)' }
                },
                y: {
                    min: -0.5, max: 0.5,
                    ticks: {
                        stepSize: 0.1,
                        color: 'var(--outline)',
                        font: { family: 'Inter', size: 10 }
                    },
                    grid: {
                        color: 'rgba(90,60,30,0.08)'
                    }
                }
            }
        },
        plugins: [
            {
                id: 'zeroLine',
                afterDraw: (chart) => {
                    const yScale = chart.scales.y;
                    const zeroY = yScale.getPixelForValue(0);
                    const ctx = chart.ctx;
                    ctx.save();
                    ctx.beginPath();
                    ctx.strokeStyle = positiveColor || '#1b4d3e';
                    ctx.lineWidth = 1.5;
                    ctx.moveTo(chart.chartArea.left, zeroY);
                    ctx.lineTo(chart.chartArea.right, zeroY);
                    ctx.stroke();
                    ctx.restore();
                }
            }
        ]
    });

    registerChart('trendChart', chart);
}

export function unmountOverview() {
    // Handled by chartManager via router
}
