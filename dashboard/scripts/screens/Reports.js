/**
 * Reports Screen — Intelligence Briefing Documents
 * Renders AI-generated news briefings in a three-zone archival layout.
 * Zones: 
 * 1. Dispatch Index (Left) — Navigation to topics
 * 2. Briefing Document (Center) — Main dossier content
 * 3. Key Actors (Right) — Entity activity (Weekly/Monthly only)
 */

let _activeTab = 'daily';
let _scrollObserver = null;

// Phase 5: Entity Stoplist
const ENTITY_STOPLIST = [
    'US', 'USA', 'UK', 'BBC', 'REUTERS', 'GLOBAL', 'NEWS', 'AFP', 'AP', 
    'DAWN', 'THE HINDU', 'REUTERS.', 'THE', 'AND', 'FOR', 'WITH', 'FROM', 'RUSSIAN'
];

function toTitleCase(str) {
    if (!str) return '';
    return str.toLowerCase().split(' ').map(word => {
        return word.charAt(0).toUpperCase() + word.slice(1);
    }).join(' ');
}

function formatPeriodLabel(label) {
    if (!label) return 'PENDING';
    const monthNames = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
    
    const formatSingle = (str) => {
        const parts = str.trim().split('-');
        if (parts.length === 3 && parts[0].length === 4) {
            const year = parts[0];
            const monthIdx = parseInt(parts[1], 10) - 1;
            if (monthIdx >= 0 && monthIdx < 12) {
                const day = parseInt(parts[2], 10);
                return `${day} ${monthNames[monthIdx]} ${year}`;
            }
        }
        return str;
    };

    if (label.includes('–')) {
        return label.split('–').map(formatSingle).join(' – ').toUpperCase();
    }
    if (label.includes(' - ')) {
        return label.split(' - ').map(formatSingle).join(' - ').toUpperCase();
    }
    return formatSingle(label).toUpperCase();
}

function parseMarkdown(text) {
  let sectionCount = 0;
  if (!text) return '';
  return text
    .replace(/^## (.+)$/gm, (_, title) => {
      const id = 'section-' + (++sectionCount);
      return `<h3 class="section-header" id="${id}">${title}</h3>`;
    })
    .replace(/^### (.+)$/gm, '<h4 class="story-title">$1</h4>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^[-•] (.+)$/gm, '<div class="watch-item"><span class="watch-bullet">▸</span><span class="watch-text">$1</span></div>')
    .replace(/^\d+\. (.+)$/gm, '<div class="watch-item"><span class="watch-bullet">▸</span><span class="watch-text">$1</span></div>')
    .replace(/\n\n/g, '</p><p class="body-text">')
    .replace(/\n/g, ' ')
    .replace(/^(.)/gm, (m) => m)
  ;
}

function isSectionHeader(line) {
    const trimmed = line.trim();
    if (!trimmed) return false;
    if (trimmed.startsWith('## ')) return true;
    if (trimmed.startsWith('### ')) return true;
    if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
        const content = trimmed.slice(2, -2).trim();
        if (/^[A-Z][A-Z\s'\u2014\u2013\-—–:]{3,}$/.test(content)) return true;
    }
    if (/^(\d+\.\s*)?[A-Z][A-Z\s'\u2014\u2013\-—–:]{4,}$/.test(trimmed)) return true;
    return false;
}

function getCleanHeader(line) {
    let trimmed = line.trim();
    if (trimmed.startsWith('## ')) {
        trimmed = trimmed.substring(3).trim();
    } else if (trimmed.startsWith('### ')) {
        trimmed = trimmed.substring(4).trim();
    } else if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
        trimmed = trimmed.slice(2, -2).trim();
    }
    return trimmed.replace(/^\d+\.\s*/, '').replace(/\s*[—–\-:]\s*$/, '').trim();
}

function normaliseBriefingHeaders(text) {
    if (!text) return '';
    const lines = text.split('\n');
    return lines.map(line => {
        const trimmed = line.trim();
        if (isSectionHeader(line) && !trimmed.startsWith('## ')) {
            return `## ${getCleanHeader(line)}`;
        }
        return line;
    }).join('\n');
}



/* ══════════════════════════════════════════════════════════
   MOUNT / UNMOUNT
   ══════════════════════════════════════════════════════════ */
export function mountReports(container, data) {
    container.innerHTML = buildShell();
    wireTabButtons(container, data);
    renderTab(container, data, _activeTab);
}

export function unmountReports() { 
    _activeTab = 'daily'; 
    if (_scrollObserver) {
        _scrollObserver.disconnect();
        _scrollObserver = null;
    }
}

/* ── Shell with Three-Zone Grid ───────────────────────────── */
function buildShell() {
    return `
        <div class="reports-layout" id="reportsLayoutContainer">
            <!-- Left Zone: Topic Index -->
            <aside class="dispatch-index" id="dispatchIndex">
                <nav id="reportsTabs" class="archive-tab-group">
                    ${['daily','weekly','monthly'].map(t => `
                        <button data-tab="${t}" class="archive-tab ${t === _activeTab ? 'archive-tab--active' : ''}">
                            ${t}
                        </button>`).join('')}
                </nav>
                <div class="index-header">TOPIC INDEX</div>
                <div id="indexList" style="flex: 1; overflow-y: auto;">
                    <!-- Topic links here -->
                </div>
            </aside>

            <!-- Center Zone: Briefing Document -->
            <main class="briefing-document" id="briefingDocument">
                <div class="retrieving-dispatch">
                    <div class="intel-pulse"></div>
                    <div class="loading-text">LOADING REPORT...</div>
                </div>
            </main>

            <!-- Right Zone: Top Entities -->
            <aside class="key-actors-rail" id="keyActorsRail">
                <div class="index-header">TOP ENTITIES</div>
                <div id="actorList" style="padding: 0;">
                    <!-- Entity bars here -->
                </div>
            </aside>
        </div>
    `;
}

function wireTabButtons(container, data) {
    container.querySelectorAll('.archive-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            _activeTab = btn.dataset.tab;
            container.querySelectorAll('.archive-tab').forEach(b => b.classList.remove('archive-tab--active'));
            btn.classList.add('archive-tab--active');
            renderTab(container, data, _activeTab);
        });
    });
}

function renderTab(container, data, tab) {
    const reports = data.reports || {};
    const report = reports[tab] || {};
    const dailyReport = reports.daily || {};
    
    // Elements
    const indexList = container.querySelector('#indexList');
    const briefingDoc = container.querySelector('#briefingDocument');
    const actorList = container.querySelector('#actorList');
    const actorRail = container.querySelector('#keyActorsRail');

    // Data Preparation
    const isFallback = report.model_used === 'Rule-based fallback';
    
    // Clean and De-duplicate entities (e.g. handle TRUMP vs TRUMP, case variations)
    const seenEntities = new Set();
    const uniqueEntities = [];
    for (const e of report.top_entities || []) {
        if (!e.text) continue;
        const norm = e.text.trim().toUpperCase();
        if (norm && !ENTITY_STOPLIST.includes(norm) && !seenEntities.has(norm)) {
            seenEntities.add(norm);
            uniqueEntities.push({
                text: toTitleCase(e.text.trim()),
                count: e.count
            });
        }
    }
    const topEntities = uniqueEntities.slice(0, 15);

    // 1. Render Center Zone (Briefing Document)
    const resolvedDailyDate = dailyReport.date || (data.daily_summary && data.daily_summary.length > 0 ? data.daily_summary[data.daily_summary.length - 1].date.replace(/_/g, '-') : '');
    renderBriefingBody(briefingDoc, report, tab, isFallback, resolvedDailyDate, reports, data);

    // 2. Render Left Zone (Dispatch Index)
    renderDispatchIndex(indexList, report, reports);

    // 3. Render Right Zone (Key Actors)
    if (tab !== 'daily' && topEntities.length > 0) {
        actorRail.style.display = 'block';
        renderKeyActors(actorList, topEntities);
    } else {
        actorRail.style.display = 'none';
    }

    // Scroll to top of document
    briefingDoc.scrollTop = 0;

    // 4. Setup Scroll-Spy and Wire Up Index Click Event Listeners
    setupScrollSpyAndEvents(indexList, briefingDoc);
}

function setupScrollSpyAndEvents(indexList, briefingDoc) {
    const indexItems = indexList.querySelectorAll('.index-item');
    const sections = briefingDoc.querySelectorAll('.section-header');

    // 1. Click navigation
    indexItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetId = item.dataset.target;
            const sectionEl = briefingDoc.querySelector(`#${targetId}`);
            if (sectionEl) {
                // Temporarily disable scroll observer during smooth scroll to prevent jank
                if (_scrollObserver) _scrollObserver.disconnect();
                
                sectionEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                
                indexItems.forEach(x => x.classList.remove('index-item--active'));
                item.classList.add('index-item--active');
                
                // Re-enable observer after smooth scroll completes
                setTimeout(() => {
                    if (_scrollObserver) {
                        sections.forEach(sec => _scrollObserver.observe(sec));
                    }
                }, 800);
            }
        });
    });

    // 2. IntersectionObserver setup
    if (_scrollObserver) {
        _scrollObserver.disconnect();
    }

    if (sections.length > 0 && 'IntersectionObserver' in window) {
        const observerOptions = {
            root: briefingDoc,
            rootMargin: '-5% 0px -75% 0px', // When section is near the top of the viewing panel
            threshold: 0
        };

        _scrollObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const targetId = entry.target.id;
                    indexItems.forEach(item => {
                        item.classList.toggle('index-item--active', item.dataset.target === targetId);
                    });
                }
            });
        }, observerOptions);

        sections.forEach(section => {
            _scrollObserver.observe(section);
        });

        // Set initial active state on first item
        if (indexItems.length > 0) {
            indexItems[0].classList.add('index-item--active');
        }
    }
}

/* ── Center Zone Renderer ─────────────────────────────────── */
function renderBriefingBody(container, report, tab, isFallback, dailyReportDate, reports, data) {
    let periodLabel = report.period || report.date || report.period_start || 'PENDING';
    
    // Meta grid data priority order
    const reportsObj = reports || {};
    const dailyReport = reportsObj.daily || {};

    let headlinesCount = report.headlines_analyzed || dailyReport.headlines_analyzed || (data && data.total_headlines);
    let sourcesCount = report.sources_count || dailyReport.sources_count;

    // Workaround lookup from details arrays
    if (data) {
        if (tab === 'daily') {
            if (data.daily_summary && data.daily_summary.length > 0) {
                const latestDaily = data.daily_summary[data.daily_summary.length - 1];
                if (latestDaily) {
                    if (!headlinesCount || headlinesCount === 0) {
                        headlinesCount = latestDaily.total_headlines;
                    }
                    if (!sourcesCount || sourcesCount === 0) {
                        sourcesCount = latestDaily.sources ? Object.keys(latestDaily.sources).length : 0;
                    }
                    if (!periodLabel || periodLabel === '' || periodLabel === 'PENDING') {
                        periodLabel = latestDaily.date ? latestDaily.date.replace(/_/g, '-') : 'PENDING';
                    }
                }
            }
        } else if (tab === 'weekly') {
            if (data.weekly_reports && data.weekly_reports.length > 0) {
                const latestWeekly = data.weekly_reports[data.weekly_reports.length - 1];
                if (latestWeekly) {
                    if (!headlinesCount || headlinesCount === 0) {
                        headlinesCount = latestWeekly.total_headlines;
                    }
                    if (!sourcesCount || sourcesCount === 0) {
                        sourcesCount = latestWeekly.source_sentiment ? Object.keys(latestWeekly.source_sentiment).length : 0;
                    }
                    if (!periodLabel || periodLabel === '' || periodLabel === ' – ' || periodLabel === 'PENDING') {
                        periodLabel = (latestWeekly.period_start && latestWeekly.period_end)
                            ? `${latestWeekly.period_start} – ${latestWeekly.period_end}`
                            : 'PENDING';
                    }
                }
            }
        } else if (tab === 'monthly') {
            if (data.monthly_reports && data.monthly_reports.length > 0) {
                const latestMonthly = data.monthly_reports[data.monthly_reports.length - 1];
                if (latestMonthly) {
                    if (!headlinesCount || headlinesCount === 0) {
                        headlinesCount = latestMonthly.total_headlines;
                    }
                    if (!sourcesCount || sourcesCount === 0) {
                        sourcesCount = latestMonthly.source_sentiment ? Object.keys(latestMonthly.source_sentiment).length : 0;
                    }
                    if (!periodLabel || periodLabel === '' || periodLabel === 'PENDING') {
                        periodLabel = (latestMonthly.period_start && latestMonthly.period_end)
                            ? `${latestMonthly.period_start} – ${latestMonthly.period_end}`
                            : 'PENDING';
                    }
                }
            }
        }
    }

    if (!headlinesCount || headlinesCount === 0) headlinesCount = '—';
    if (!sourcesCount || sourcesCount === 0) sourcesCount = '—';

    let clustersCount = '—';
    if (report.clusters && Array.isArray(report.clusters)) {
        clustersCount = report.clusters.length;
    } else if (dailyReport.clusters && Array.isArray(dailyReport.clusters)) {
        clustersCount = dailyReport.clusters.length;
    } else {
        const text = report.briefing || '';
        const normalised = normaliseBriefingHeaders(text);
        const count = (normalised.match(/^## /gm) || []).length;
        if (count > 0) {
            clustersCount = count;
        }
    }

    // Stale Content Guard Match Check
    const todayStr = new Date().toISOString().slice(0, 10);
    const isStale = !dailyReportDate || dailyReportDate !== todayStr;

    container.innerHTML = `
        <div class="paper-sheet">
            ${isFallback ? `
                <div style="background:var(--primary);color:white;padding:4px 12px;font-family:var(--font-mono);font-size:0.7rem;font-weight:900;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:2rem;display:inline-block">
                    FALLBACK REPORT: SYNTHESIZED VIA RULE-BASED LOGIC
                </div>
            ` : ''}

            ${isStale ? `
                <div style="font-family: 'Inter', sans-serif; font-size: 10px; font-style: italic; color: var(--outline); margin-bottom: 12px;">
                    * Showing archived briefing from ${dailyReportDate || 'unknown'} — today's data pending
                </div>
            ` : ''}

            <header class="briefing-header" style="border: none; padding-bottom: 0; margin-bottom: 0;">
                <div class="period-badge">${tab.toUpperCase()} — ${formatPeriodLabel(periodLabel)}</div>
            </header>
            <hr class="briefing-hr" style="border: 0; border-top: 1px solid var(--outline); margin: 0 0 20px 0;">

            <div class="meta-grid">
                <div class="meta-cell">
                    <span class="meta-value">${headlinesCount}</span>
                    <span class="meta-label">Headlines</span>
                </div>
                <div class="meta-cell">
                    <span class="meta-value">${sourcesCount}</span>
                    <span class="meta-label">Sources</span>
                </div>
                <div class="meta-cell">
                    <span class="meta-value">${clustersCount}</span>
                    <span class="meta-label">Clusters</span>
                </div>
            </div>

            <article class="briefing-article">
                ${'<p class="body-text">' + parseMarkdown(normaliseBriefingHeaders(report.briefing)) + '</p>'}
            </article>

            <footer style="margin-top: 60px; padding-top: 20px; border-top: 1px dashed var(--outline); font-family: 'Shadows Into Light', cursive; font-size: 1.15rem; color: var(--outline); display: flex; justify-content: space-between; align-items: center; line-height: 1.6;">
                <span>Report synthesized from ${headlinesCount} headlines across ${sourcesCount} sources.</span>
                ${report.model_used ? `<span>Model: ${report.model_used}</span>` : ''}
            </footer>
        </div>
    `;
}

/* ── Left Zone Renderer ───────────────────────────────────── */
function renderDispatchIndex(container, report, reports) {
    const text = report.briefing;
    const reportsObj = reports || {};
    
    // Cluster-based topic index
    const clusters = report.clusters || (reportsObj.daily && reportsObj.daily.clusters);
    if (clusters && Array.isArray(clusters) && clusters.length > 0) {
        container.innerHTML = clusters.map((c, idx) => {
            const topicName = c.topic || c.name || "";
            const countLabel = c.count !== undefined && c.count !== null ? `[${c.count}]` : (idx + 1).toString().padStart(2, '0');
            return `
                <div class="index-item" data-target="section-${idx + 1}">
                    <span class="index-item__label">${topicName}</span>
                    <span class="index-item__count">${countLabel}</span>
                </div>
            `;
        }).join('');
        return;
    }

    console.warn('clusters not in JSON — using section fallback');

    if (!text) {
        container.innerHTML = '<div style="padding:1rem;font-style:italic;opacity:0.5">No index available</div>';
        return;
    }

    // Normalise and extract headers
    const normalised = normaliseBriefingHeaders(text);
    const sections = [];
    normalised.split('\n').forEach(line => {
        if (line.startsWith('## ')) {
            sections.push(line.substring(3).trim());
        }
    });

    if (sections.length === 0) {
        container.innerHTML = '<div style="padding:1rem;font-style:italic;opacity:0.5">Automated Indexing Failed</div>';
        return;
    }

    container.innerHTML = sections.map((section, idx) => `
        <div class="index-item" data-target="section-${idx + 1}">
            <span class="index-item__label">${section}</span>
            <span class="index-item__count">${(idx + 1).toString().padStart(2, '0')}</span>
        </div>
    `).join('');
}

/* ── Right Zone Renderer ──────────────────────────────────── */
function renderKeyActors(container, entities) {
    const maxCount = Math.max(...entities.map(e => e.count));
    
    container.innerHTML = entities.map(e => {
        const percentage = (e.count / maxCount) * 100;
        return `
            <div class="actor-item" style="display: flex; flex-direction: column; gap: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                    <span class="actor-name" style="margin-bottom: 0; color: var(--text);">${e.text}</span>
                    <span style="font-family: 'Courier New', Courier, monospace; font-size: 0.75rem; color: var(--primary); font-weight: 700;">[${e.count}]</span>
                </div>
                <div class="actor-bar-wrap" style="height: 6px; background: rgba(90, 60, 30, 0.08); border: 1px solid var(--outline); width: 100%;">
                    <div class="actor-bar" style="width: ${percentage}%; background: var(--primary); height: 100%;"></div>
                </div>
            </div>
        `;
    }).join('');
}

/* ── Briefing Parser (Updated for Phase 4) ────────────────── */
function parseAndStyleBriefing(text) {
    if (!text) return '<p style="font-style:italic;opacity:0.5">No data content retrieved.</p>';

    const lines = text.split('\n');
    let html = '';
    let inList = false;
    let sectionIdx = 0;
    let inSection = false;

    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) {
            if (inList) { html += '</ul>'; inList = false; }
            continue;
        }

        // Section Headers
        const isHeader = /^(\d+\.\s*)?[A-Z][A-Z\s'\u2014\u2013\-—–:]{4,}$/.test(trimmed);

        if (isHeader) {
            if (inList) { html += '</ul>'; inList = false; }
            if (inSection) { html += '</div></section>'; }
            
            const cleanHeader = trimmed.replace(/^\d+\.\s*/, '').replace(/\s*[—–\-:]\s*$/, '');
            html += `
                <section class="briefing-section" id="section-${sectionIdx++}">
                    <div class="section-label">${cleanHeader}</div>
                    <div class="section-content">
            `;
            inSection = true;
            continue;
        }

        // List items
        if (/^[\u2022•\-\*]\s/.test(trimmed) || /^\d+\)\s/.test(trimmed)) {
            if (!inList) { html += '<ul style="margin: 1rem 0 1.5rem 1.2rem; list-style-type: square;">'; inList = true; }
            const bulletText = trimmed.replace(/^[\u2022•\-\*]\s*/, '').replace(/^\d+\)\s*/, '');
            html += `<li style="margin-bottom: 0.8rem;">${bulletText}</li>`;
            continue;
        }

        // Paragraph
        if (inList) { html += '</ul>'; inList = false; }
        
        // If not in a section yet (e.g. intro text), wrap it anyway or just append
        html += `<p style="margin-bottom: 1.5rem;">${trimmed}</p>`;
    }

    if (inList) html += '</ul>';
    if (inSection) html += '</div></section>';
    
    return html;
}

