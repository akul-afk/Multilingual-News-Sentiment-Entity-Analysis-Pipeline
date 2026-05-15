import { registerChart } from '../utils/chartManager.js';
import { iconArrowUp, iconArrowDown, iconTrendUp, iconTrendDown } from '../icons.js';

export function mountOverview(container, data) {
    const latestReport = data.weekly_reports?.[0] || {};
    const trends = data.daily_summary || [];

    container.innerHTML = `
        <div class="page-title">
            <p>Strategic news summary across ${Object.keys(latestReport.source_sentiment || {}).length || 6} global sources.</p>
        </div>

        <div class="grid grid--3 mt-8">
            <div class="torn-wrapper">
                <div class="torn-container kpi">
                    <span class="card-category">Strategic Reach</span>
                    <h3 class="card-title">TOTAL MENTIONS</h3>
                    <div class="kpi__value">${data.total_headlines || latestReport.total_headlines || 0}</div>
                    <div class="kpi__change kpi__change--up flex items-center gap-1">${iconTrendUp(14)} 12% vs last week</div>
                </div>
            </div>
            <div class="torn-wrapper">
                <div class="torn-container kpi">
                    <span class="card-category">Sentiment Axis</span>
                    <h3 class="card-title">AVG POLARITY</h3>
                    <div class="kpi__value">
                        ${latestReport.avg_polarity > 0 ? '+' : ''}${latestReport.avg_polarity?.toFixed(2) || '0.00'}
                    </div>
                    <div class="kpi__change ${latestReport.avg_polarity > 0 ? 'kpi__change--up' : 'kpi__change--down'} flex items-center gap-1">
                        ${latestReport.avg_polarity > 0 ? iconArrowUp(14) : iconArrowDown(14)}
                        ${latestReport.avg_polarity > 0 ? 'Improving' : 'Declining'}
                    </div>
                </div>
            </div>
            <div class="torn-wrapper">
                <div class="torn-container kpi">
                    <span class="card-category">Entity Network</span>
                    <h3 class="card-title">ENTITIES TRACKED</h3>
                    <div class="kpi__value">${data.total_entities || 0}</div>
                    <div class="kpi__change">Stable</div>
                </div>
            </div>
        </div>

        <div class="grid grid--65-35 mt-8">
            <div class="torn-wrapper">
                <div class="torn-container">
                    <span class="card-category">Temporal Intelligence</span>
                    <h3 class="card-title">Sentiment Trend (Last 30 Days)</h3>
                    <div class="chart-area" style="height: 300px;">
                        <canvas id="trendChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="torn-wrapper">
                <div class="torn-container">
                    <span class="card-category">Latest Dispatches</span>
                    <h3 class="card-title">Top Headlines</h3>
                    <div class="headline-ticker-list" style="max-height: 300px; overflow-y: auto; padding-right: 10px;">
                        <ul class="list-ink">
                            ${(latestReport.top_stories || []).slice(0, 10).map(s => `
                                <li style="margin-bottom: 1rem; border-bottom: 1px dashed var(--outline); padding-bottom: 0.5rem;">
                                    <div style="font-family: var(--font-heading); font-weight: 700; font-size: 0.9rem;">${s.Translated_Headline}</div>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    `;

    const ctx = document.getElementById('trendChart').getContext('2d');
    
    // Take last 30 points for the trend chart
    const chartTrends = trends.slice(-30);
    
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartTrends.map(t => t.date.replace(/_/g, '/')),
            datasets: [{
                label: 'Global Polarity',
                data: chartTrends.map(t => t.avg_polarity),
                borderColor: '#5a3c1e',
                backgroundColor: 'rgba(90, 60, 30, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 2,
                pointBackgroundColor: '#5a3c1e'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#f4e9d9',
                    titleColor: '#2d1b0d',
                    bodyColor: '#2d1b0d',
                    borderColor: '#5a3c1e',
                    borderWidth: 1,
                    cornerRadius: 0
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

    registerChart('trendChart', chart);
}

export function unmountOverview() {
    // Handled by chartManager via router
}
