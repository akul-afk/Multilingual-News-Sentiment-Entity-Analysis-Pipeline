import { ENTITY_COLORS } from '../utils/constants.js';
import { drawNetwork } from '../utils/networkGraph.js';
import { iconSearch, iconTarget, iconReport, iconShield } from '../icons.js';

export function mountEntityExplorer(container, data) {
    const allEntities = data.entities?.entities || [];
    const coOccurrences = data.entities?.co_occurrence || [];
    
    // Sort entities by count descending
    const sortedEntities = [...allEntities].sort((a, b) => (b.count || 0) - (a.count || 0));

    // Calculate informatics
    const avgMentions = sortedEntities.reduce((acc, curr) => acc + curr.count, 0) / sortedEntities.length;
    const highReachEntities = sortedEntities.filter(e => (e.count || 0) > avgMentions * 2).length;
    const polarizingEntities = sortedEntities.filter(e => Math.abs(e.avg_sentiment || 0) > 0.4).length;

    container.innerHTML = `
        <div class="page-title">
            <h1>Entity Intelligence</h1>
            <p>Classified ledger of actors, locations, and narrative-driving entities.</p>
        </div>

        <div class="grid grid--3 mb-8">
            <div class="torn-wrapper">
                <div class="torn-container kpi" style="padding-bottom: 2rem;">
                    <span class="card-category">Strategic Presence</span>
                    <h3 class="card-title">SIGNAL REACH</h3>
                    <div class="kpi__value">${highReachEntities}</div>
                    <span class="kpi__label-sketch">High-Impact Actors</span>
                </div>
            </div>
            <div class="torn-wrapper">
                <div class="torn-container kpi" style="padding-bottom: 2rem;">
                    <span class="card-category">Narrative Friction</span>
                    <h3 class="card-title">POLARIZATION</h3>
                    <div class="kpi__value">${polarizingEntities}</div>
                    <span class="kpi__label-sketch">Polarized Coverage</span>
                </div>
            </div>
            <div class="torn-wrapper">
                <div class="torn-container kpi" style="padding-bottom: 2rem;">
                    <span class="card-category">System Ledger</span>
                    <h3 class="card-title">INTELLIGENCE TIER</h3>
                    <div class="kpi__value flex items-center justify-center gap-2" style="font-size: 2.2rem; margin-top: 1rem;">
                        ${iconShield(32)} SECURE
                    </div>
                    <span class="kpi__label-sketch">Level 4 Access</span>
                </div>
            </div>
        </div>

        <div class="filter-masthead mb-6" style="padding: 10px 0; display: flex; gap: 20px; align-items: center; border-bottom: 2px solid var(--outline);">
            <span style="font-family: var(--font-heading); font-weight: 900; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px;">Classified Filter:</span>
            <div id="entityTypeFilters" style="display: flex; gap: 10px;">
                <button class="torn-button torn-button--active" data-type="ALL">ALL RECORDS</button>
                <button class="torn-button" data-type="PER">PERSONS</button>
                <button class="torn-button" data-type="ORG">ORGANIZATIONS</button>
                <button class="torn-button" data-type="GPE">REGIONS/GPE</button>
            </div>
        </div>

        <div class="grid grid--2 mb-8" style="grid-template-columns: 1fr 1.5fr; gap: 2rem;">
            <div class="torn-wrapper">
                <div class="torn-container" id="entityDossier" style="min-height: 500px; transition: all 0.3s ease;">
                    <div class="dossier-empty" style="text-align: center; padding-top: 4rem; opacity: 0.3;">
                        <div class="mb-4 flex justify-center">${iconSearch(60)}</div>
                        <p class="italic">Select an entity from the ledger to view classified dossier.</p>
                    </div>
                </div>
            </div>

            <div class="torn-wrapper">
                <div class="torn-container" style="padding: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 2px solid var(--outline); padding-bottom: 1rem;">
                        <div>
                            <span class="card-category">Census Registry</span>
                            <h3 class="card-title" style="border: none; padding: 0; margin: 0;">Intelligence Ledger</h3>
                        </div>
                        <div class="search-box" style="position: relative;">
                            <input type="text" id="entitySearch" placeholder="Search actor files..." 
                                   style="background: var(--surface-low); border: 1px solid var(--outline); padding: 0.6rem 1.2rem; font-family: var(--font-body); color: var(--text); border-radius: 0; width: 220px; font-style: italic; border-bottom: 2px solid var(--outline);">
                        </div>
                    </div>
                    <div class="ledger-container" style="max-height: 480px; overflow-y: auto;">
                        <table class="table-vintage" style="width: 100%; border-collapse: collapse;">
                            <thead style="position: sticky; top: 0; background: var(--surface); z-index: 10;">
                                <tr style="border-bottom: 2px solid var(--outline);">
                                    <th style="text-align: left; padding: 1rem; font-size: 0.7rem; text-transform: uppercase;">Entity Name</th>
                                    <th style="text-align: left; padding: 1rem; font-size: 0.7rem; text-transform: uppercase;">Type</th>
                                    <th style="text-align: right; padding: 1rem; font-size: 0.7rem; text-transform: uppercase;">Signal Strength</th>
                                </tr>
                            </thead>
                            <tbody id="entityTableBody">
                                <!-- Populated by updateLedger -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <div class="torn-wrapper mt-8">
            <div class="torn-container">
                <span class="card-category">Relational Network</span>
                <h3 class="card-title">NARRATIVE ASSOCIATIONS</h3>
                <div class="connection-map" style="position: relative; height: 500px; background: rgba(90, 60, 30, 0.02); border: 1px dashed var(--outline);">
                    <canvas id="networkCanvas" style="width: 100%; height: 100%;"></canvas>
                    <div style="position: absolute; top: 20px; right: 20px; text-align: right; pointer-events: none;">
                        <p class="italic text-xs" style="margin: 0; opacity: 0.6;">Orbital mapping: entities co-mentioned in headlines.</p>
                        <p class="bold text-xs" style="margin: 0; color: var(--primary);">N=15 Primary Nodes</p>
                    </div>
                </div>
            </div>
        </div>
    `;

    // State for filtering
    let currentType = 'ALL';
    let searchQuery = '';
    const tableBody = document.getElementById('entityTableBody');
    const dossier = document.getElementById('entityDossier');

    function updateDossier(entity) {
        const sentiment = entity.avg_sentiment || 0;
        const sentClass = sentiment > 0.2 ? 'text-pos' : (sentiment < -0.2 ? 'text-neg' : '');
        const sentLabel = sentiment > 0.2 ? 'POSITIVE BIAS' : (sentiment < -0.2 ? 'NEGATIVE BIAS' : 'NEUTRAL TONE');
        
        // Find connections for this entity
        const entityConnections = coOccurrences
            .filter(co => co[0] === entity.name || co[1] === entity.name)
            .map(co => co[0] === entity.name ? co[1] : co[0])
            .slice(0, 5);

        dossier.innerHTML = `
            <div class="dossier-active" style="padding: 1.5rem;">
                <div style="text-align: center; border-bottom: 2px double var(--outline); padding-bottom: 1.5rem; margin-bottom: 1.5rem;">
                    <span class="card-category" style="background: var(--outline); color: var(--bg); padding: 2px 8px;">FILE ID: ${entity.label}-${Math.floor(Math.random()*9000)+1000}</span>
                    <h2 style="font-family: var(--font-heading); font-size: 2.2rem; margin: 0.5rem 0; text-transform: uppercase; line-height: 1;">${entity.name}</h2>
                    <span class="badge" style="border-color: var(--primary); color: var(--primary);">${entity.label}</span>
                </div>

                <div class="list-ink" style="display: flex; flex-direction: column; gap: 1rem;">
                    <div style="background: var(--surface-low); padding: 1rem; border: 1px solid var(--outline); border-left: 4px solid var(--primary);">
                        <span class="card-category" style="font-size: 0.6rem;">Intelligence Assessment</span>
                        <h4 style="margin: 0; font-family: var(--font-heading);">${sentLabel}</h4>
                        <div style="height: 6px; background: var(--surface-highest); margin: 8px 0; position: relative;">
                            <div style="position: absolute; left: 50%; top: -4px; height: 14px; width: 2px; background: var(--outline);"></div>
                            <div style="position: absolute; left: ${50 + (sentiment * 50)}%; top: -2px; height: 10px; width: 10px; background: var(--primary); transform: translateX(-50%); border-radius: 50%;"></div>
                        </div>
                        <p class="text-xs italic" style="margin: 0; opacity: 0.8;">Sentiment polarity extracted via neural narrative analysis.</p>
                    </div>

                    <div>
                        <span class="card-category" style="font-size: 0.6rem;">Frequency Profile</span>
                        <div style="display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px dashed var(--outline); padding: 5px 0;">
                            <span class="bold text-sm">TOTAL MENTIONS</span>
                            <span class="kpi__value" style="font-size: 1.5rem; margin: 0;">${entity.count}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px dashed var(--outline); padding: 5px 0;">
                            <span class="bold text-sm">SIGNAL REACH</span>
                            <span class="bold" style="font-size: 1rem;">${Math.min(Math.ceil(entity.count / 5), 100)}%</span>
                        </div>
                    </div>

                    <div style="margin-top: 1rem;">
                        <span class="card-category" style="font-size: 0.6rem;">Narrative Affiliates</span>
                        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;">
                            ${entityConnections.length > 0 ? entityConnections.map(conn => `
                                <span class="badge" style="font-size: 0.65rem; background: var(--surface-highest); border-style: dotted;">${conn}</span>
                            `).join('') : '<p class="text-xs italic opacity-50">No primary connections identified in current dataset.</p>'}
                        </div>
                    </div>

                    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--outline);">
                        <p class="text-xs" style="line-height: 1.6; opacity: 0.8;">
                            <span class="bold">OBSERVATION:</span> This entity currently maintains a 
                            <span class="bold ${sentClass}">${sentiment > 0 ? 'prominent' : 'critical'} focus</span> 
                            across global dispatches. Continued monitoring of co-occurrences recommended.
                        </p>
                    </div>
                </div>
            </div>
        `;
    }

    function updateLedger() {
        const filtered = sortedEntities.filter(en => {
            const matchesType = currentType === 'ALL' || en.label === currentType;
            const matchesSearch = en.name.toLowerCase().includes(searchQuery) || 
                                en.label.toLowerCase().includes(searchQuery);
            return matchesType && matchesSearch;
        });

        tableBody.innerHTML = filtered.map(entity => {
            const color = ENTITY_COLORS[entity.label] || 'var(--outline)';
            return `
                <tr class="ledger-row" data-name="${entity.name}" style="border-bottom: 1px dashed var(--outline); transition: all 0.2s ease; cursor: pointer;">
                    <td style="padding: 1rem; font-family: var(--font-heading); font-weight: 700;">${entity.name}</td>
                    <td style="padding: 1rem;">
                        <span class="badge" style="border-color: ${color}; color: ${color}; font-size: 0.6rem; padding: 2px 6px;">${entity.label}</span>
                    </td>
                    <td style="padding: 1rem; text-align: right;">
                        <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px;">
                            <span style="font-weight: bold; font-family: var(--font-heading); font-size: 1.1rem;">${entity.count}</span>
                            <div style="width: 40px; height: 4px; background: var(--surface-highest); overflow: hidden;">
                                <div style="width: ${Math.min(entity.count / sortedEntities[0].count * 100, 100)}%; height: 100%; background: var(--primary);"></div>
                            </div>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        // Add click listeners to rows
        document.querySelectorAll('.ledger-row').forEach(row => {
            row.addEventListener('click', () => {
                const name = row.dataset.name;
                const entity = sortedEntities.find(e => e.name === name);
                document.querySelectorAll('.ledger-row').forEach(r => r.style.background = 'transparent');
                row.style.background = 'var(--surface-highest)';
                updateDossier(entity);
            });
        });

        if (filtered.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="3" style="padding: 4rem; text-align: center; font-style: italic; color: var(--text-muted); opacity: 0.5;">ARCHIVE SEARCH RETURNED NULL: No records match criteria.</td></tr>`;
        }
    }

    // Initialize Network Graph with a small delay
    setTimeout(() => {
        const canvas = document.getElementById('networkCanvas');
        if (canvas) {
            drawNetwork(canvas, coOccurrences);
        }
    }, 300);

    // Initial Ledger Load
    updateLedger();

    // Event Listeners
    const searchInput = document.getElementById('entitySearch');
    const filterButtons = document.querySelectorAll('#entityTypeFilters .torn-button');

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value.toLowerCase();
            updateLedger();
        });
    }

    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('torn-button--active'));
            btn.classList.add('torn-button--active');
            currentType = btn.dataset.type;
            updateLedger();
        });
    });
}



export function unmountEntityExplorer() {
    // No specific cleanup needed
}
