export function mountReports(container, data) {
    const reports = data.weekly_reports || [];
    const latest = reports[0] || {};
    const aiDigest = latest.summary || "No automated intelligence summary available.";
    const keyTakeaways = latest.key_takeaways || [];

    container.innerHTML = `
        <div class="page-title">
            <div style="display: flex; gap: 1rem;">
                <button class="badge-ink" style="cursor: pointer;" onclick="window.print()">PRINT RECORD</button>
                <button class="badge-ink" style="cursor: pointer; background: var(--primary); color: white;">DOWNLOAD ARCHIVE</button>
            </div>
        </div>
        
        <div class="torn-wrapper">
            <div class="torn-container" style="padding: 4rem; position: relative; overflow: hidden;">
                <span class="card-category">Classified Briefing</span>
                <h3 class="card-title">Weekly Intelligence Summary</h3>
                
                <!-- Watermark/Seal -->
                <div style="position: absolute; top: 2rem; right: 2rem; opacity: 0.1; transform: rotate(15deg);">
                    <svg width="150" height="150" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="5,2"/>
                        <text x="50" y="55" font-family="var(--font-heading)" font-weight="900" font-size="12" text-anchor="middle" fill="currentColor">OFFICIAL SEAL</text>
                    </svg>
                </div>

                <div style="text-align: center; border-bottom: 4px double var(--outline); padding-bottom: 2rem; margin-bottom: 3rem; margin-top: 2rem;">
                    <div style="font-family: var(--font-heading); font-size: 2.5rem; letter-spacing: -1px; margin-bottom: 0.5rem;">GLOBAL NEWS PULSE</div>
                    <div style="font-family: var(--font-sketch); font-size: 1.2rem; color: var(--primary);">Intelligence Analysis Bureau</div>
                    <div class="mt-4" style="font-weight: 700; text-transform: uppercase; border: 2px solid var(--outline); display: inline-block; padding: 0.25rem 1rem;">
                        PERIOD: ${latest.label || 'CURRENT WEEK'}
                    </div>
                </div>
                
                <section class="mt-8">
                    <h2 style="font-family: var(--font-heading); font-size: 1.8rem; border-bottom: 1px solid var(--outline); padding-bottom: 0.5rem; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 1rem;">
                        <span style="font-size: 1.2rem; background: var(--text); color: white; padding: 0 0.5rem;">I</span> 
                        Situation Summary
                    </h2>
                    <div style="font-size: 1.1rem; line-height: 1.8; color: var(--text); text-align: justify; columns: 2; column-gap: 3rem;">
                        ${aiDigest}
                    </div>
                </section>

                <section class="mt-12">
                    <h2 style="font-family: var(--font-heading); font-size: 1.8rem; border-bottom: 1px solid var(--outline); padding-bottom: 0.5rem; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 1rem;">
                        <span style="font-size: 1.2rem; background: var(--text); color: white; padding: 0 0.5rem;">II</span> 
                        Key Intelligence Takeaways
                    </h2>
                    <ul class="list-ink" style="columns: 1; font-size: 1.1rem;">
                        ${keyTakeaways.length > 0 ? keyTakeaways.map(k => `
                            <li style="margin-bottom: 1rem; border-left: 3px solid var(--outline); padding-left: 1.5rem; position: relative;">
                                ${k}
                            </li>
                        `).join('') : '<li class="italic">No specific takeaways recorded for this period.</li>'}
                    </ul>
                </section>

                <div class="mt-16" style="display: flex; justify-content: space-between; align-items: flex-end; border-top: 1px solid var(--outline); padding-top: 2rem;">
                    <div>
                        <div style="font-family: var(--font-sketch); font-size: 1.8rem; color: var(--primary); margin-bottom: -0.5rem;">Verified</div>
                        <div style="font-size: 0.8rem; opacity: 0.7;">Chief Intelligence Officer</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: 900; text-transform: uppercase; font-size: 0.9rem;">GNP Document Archive</div>
                        <div style="font-size: 0.7rem; color: var(--text-dim); font-family: monospace;">UUID: ${Math.random().toString(36).substr(2, 9).toUpperCase()}-${Date.now()}</div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

export function unmountReports() {}
