import { SOURCE_COLORS } from '../utils/constants.js';
import { registerChart } from '../utils/chartManager.js';
import { iconTrendUp, iconTrendDown } from '../icons.js';

export function mountCrossLanguage(container, data) {
    const weeklyReports = data.weekly_reports || [];
    const latest = weeklyReports[0] || {};
    const previous = weeklyReports[1] || {};

    const sources = Object.keys(latest.source_sentiment || {});
    const latestSent = latest.source_sentiment || {};
    const prevSent = previous.source_sentiment || {};

    container.innerHTML = `
        <div class="page-title">
            <h1>Cross-Language Analysis</h1>
            <p>Comparative sentiment divergence across global language services.</p>
        </div>

        <div class="grid grid--65-35">
            <div class="torn-wrapper">
                <div class="torn-container">
                    <span class="card-category">Divergence Index</span>
                    <h3 class="card-title">Sentiment Polarity by Dispatch</h3>
                    <div class="chart-area" style="height: 400px;">
                        <canvas id="crossLangChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="torn-wrapper">
                <div class="torn-container">
                    <span class="card-category">Narrative Shift</span>
                    <h3 class="card-title">Trend Divergence</h3>
                    <div class="divergence-ledger" style="max-height: 400px; overflow-y: auto;">
                        ${renderDivergence(latestSent, prevSent)}
                    </div>
                </div>
            </div>
        </div>
    `;

    const ctx = document.getElementById('crossLangChart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sources.map(s => s.replace('BBC ', '')),
            datasets: [
                {
                    label: 'Current Briefing',
                    data: sources.map(s => latestSent[s]),
                    backgroundColor: '#5a3c1e',
                    borderWidth: 0,
                    borderRadius: 0,
                    barPercentage: 0.6
                },
                {
                    label: 'Prior Archive',
                    data: sources.map(s => prevSent[s] || 0),
                    backgroundColor: 'rgba(90, 60, 30, 0.15)',
                    borderWidth: 0,
                    borderRadius: 0,
                    barPercentage: 0.6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    position: 'bottom',
                    labels: { font: { family: 'var(--font-body)', size: 12 } }
                }
            },
            scales: {
                y: { 
                    min: -0.5, 
                    max: 0.5,
                    grid: { color: 'rgba(90, 60, 30, 0.1)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });

    registerChart('crossLangChart', chart);
}

function renderDivergence(current, previous) {
    const changes = Object.keys(current).map(source => {
        const curr = current[source];
        const prev = previous[source] || 0;
        const diff = curr - prev;
        return { source, diff, curr, prev };
    }).sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff));

    return changes.map(item => {
        const isDivergent = Math.abs(item.diff) > 0.15;
        const icon = item.diff > 0 ? iconTrendUp(14) : iconTrendDown(14);
        const colorClass = item.diff > 0 ? 'text-pos' : 'text-neg';
        
        if (isDivergent) {
            return `
                <div class="torn-wrapper mt-4 mb-4">
                    <div class="torn-container" style="padding: 1rem; background: var(--surface-highest);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="font-family: var(--font-heading); font-weight: 700; font-size: 0.9rem;">${item.source}</div>
                             <div class="${colorClass} flex items-center gap-1" style="font-weight: 900; font-family: var(--font-sketch);">
                                ${icon} ${item.diff > 0 ? '+' : ''}${item.diff.toFixed(2)}
                            </div>
                        </div>
                        <div style="font-size: 0.65rem; opacity: 0.8; font-style: italic; border-top: 1px dashed var(--outline); margin-top: 0.5rem; padding-top: 0.5rem;">
                            DIVERGENCE DETECTED: Shifted from ${item.prev.toFixed(2)} to ${item.curr.toFixed(2)}
                        </div>
                    </div>
                </div>
            `;
        }

        return `
            <div style="padding: 0.75rem 0.5rem; border-bottom: 1px dashed var(--outline); opacity: 0.8;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-family: var(--font-heading); font-size: 0.85rem;">${item.source}</div>
                    <div class="${colorClass}" style="font-weight: bold;">
                        ${item.diff > 0 ? '+' : ''}${item.diff.toFixed(2)}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

export function unmountCrossLanguage() {}
