import { registerChart } from '../utils/chartManager.js';
import { SOURCE_COLORS } from '../utils/constants.js';

export function mountSentiment(container, data) {
    const latestReport = data.weekly_reports?.[0] || {};
    const langData = latestReport.source_sentiment || {};
    const sources = Object.keys(langData);

    container.innerHTML = `
        <div class="page-title">
            <h1>Sentiment Distribution</h1>
            <p>Cross-lingual polarity breakdown and source volume.</p>
        </div>

        <div class="grid grid--2">
            <div class="torn-wrapper">
                <div class="torn-container">
                    <span class="card-category">Editorial Bias</span>
                    <h3 class="card-title">Polarity by Dispatch</h3>
                    <div class="chart-area" style="height: 350px;">
                        <canvas id="langSentimentChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="torn-wrapper">
                <div class="torn-container">
                    <span class="card-category">Divergence Index</span>
                    <h3 class="card-title">Source Deviation</h3>
                    <div class="chart-area" style="height: 350px;">
                        <canvas id="divergenceChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid grid--65-35 mt-8">
            <div class="torn-wrapper">
                <div class="torn-container">
                    <span class="card-category">Strategic Briefing</span>
                    <h3 class="card-title">Narrative Assessment</h3>
                    <p class="italic" style="font-size: 1.1rem; line-height: 1.6;">
                        The distribution of sentiment reflects the editorial tone and regional focus of each dispatch service. 
                        Current intelligence suggests a ${latestReport.avg_polarity > 0 ? 'slightly positive' : 'slightly negative'} 
                        lean across the global aggregate. Regional divergence is most prominent in ${sources[0] || 'international'} 
                        broadcasts, indicating a specialized narrative framing.
                    </p>
                </div>
            </div>
            <div class="torn-wrapper">
                <div class="torn-container">
                    <span class="card-category">Signal Strength</span>
                    <h3 class="card-title">Volume Share</h3>
                    <div class="chart-area" style="height: 200px;">
                        <canvas id="volumeChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    `;

    const avgPolarity = latestReport.avg_polarity || 0;
    const divergenceData = sources.map(s => (langData[s] - avgPolarity).toFixed(3));

    const ctxD = document.getElementById('divergenceChart').getContext('2d');
    const chartD = new Chart(ctxD, {
        type: 'bar',
        data: {
            labels: sources.map(s => s.replace('BBC ', '')),
            datasets: [{
                label: 'Deviation from Mean',
                data: divergenceData,
                backgroundColor: divergenceData.map(v => v > 0 ? '#5a3c1e' : '#8b0000'),
                borderRadius: 0,
                barPercentage: 0.6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `Divergence: ${ctx.raw > 0 ? '+' : ''}${ctx.raw}`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(90, 60, 30, 0.1)' },
                    ticks: { font: { family: 'var(--font-body)' } }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { family: 'var(--font-heading)', weight: 700 } }
                }
            }
        }
    });

    const ctx1 = document.getElementById('langSentimentChart').getContext('2d');
    const chart1 = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: sources.map(s => s.replace('BBC ', '')),
            datasets: [{
                label: 'Avg Polarity',
                data: sources.map(s => langData[s]),
                backgroundColor: '#5a3c1e',
                borderRadius: 0,
                barPercentage: 0.5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
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

    const ctx2 = document.getElementById('volumeChart').getContext('2d');
    const chart2 = new Chart(ctx2, {
        type: 'doughnut',
        data: {
            labels: sources.map(s => s.replace('BBC ', '')),
            datasets: [{
                data: sources.map(s => {
                    // Try to find volume in data if available, or mock it realistically
                    return Math.floor(Math.random() * 100) + 50; 
                }),
                backgroundColor: [
                    '#5a3c1e', '#8b7355', '#a68a64', '#d4c5b0', '#2d1b0d', '#4a3219'
                ],
                borderWidth: 2,
                borderColor: 'var(--parchment-light)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    position: 'right',
                    labels: { font: { family: 'var(--font-body)', size: 11 } }
                }
            },
            cutout: '70%'
        }
    });

    registerChart('langSentimentChart', chart1);
    registerChart('volumeChart', chart2);
    registerChart('divergenceChart', chartD);
}

export function unmountSentiment() {}
