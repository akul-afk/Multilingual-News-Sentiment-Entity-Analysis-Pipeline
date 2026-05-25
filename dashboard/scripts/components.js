import { auth } from './utils/auth.js';
import { 
    iconOverview, iconActivity, iconGlobe, iconSearch, iconMap, iconReport, iconRefresh, iconTarget 
} from './icons.js';

export function renderSidebar(container) {
    const isGuest = auth.getRole() === 'guest';
    container.innerHTML = `
        <div class="sidebar__logo">
            <div class="sidebar__logo-icon">G</div>
            <h2 class="sidebar__logo-text">Global News Pulse</h2>
            <p class="sidebar__logo-sub">ANALYSIS & METRICS</p>
            ${isGuest ? '<div class="badge badge--primary italic mt-2">Guest Edition</div>' : ''}
        </div>
        <nav class="sidebar__nav">
            <a href="#overview" class="sidebar__link" data-hash="#overview">
                <span class="sidebar__link-icon">${iconOverview(16)}</span> Overview
            </a>
            <a href="#sentiment" class="sidebar__link" data-hash="#sentiment">
                <span class="sidebar__link-icon">${iconActivity(16)}</span> Sentiment
            </a>
            <a href="#cross" class="sidebar__link" data-hash="#cross">
                <span class="sidebar__link-icon">${iconGlobe(16)}</span> Cross-Language
            </a>
            <a href="#entities" class="sidebar__link" data-hash="#entities">
                <span class="sidebar__link-icon">${iconSearch(16)}</span> Entity Explorer
            </a>
            <a href="#geo" class="sidebar__link" data-hash="#geo">
                <span class="sidebar__link-icon">${iconMap(16)}</span> Geo Heatmap
            </a>
            <a href="#reports" class="sidebar__link" data-hash="#reports">
                <span class="sidebar__link-icon">${iconReport(16)}</span> Reports
            </a>
        </nav>
        <div class="sidebar__footer">
            <div class="sidebar__status mb-2">
                <span class="sidebar__status-dot pulse-dot"></span>
                Pipeline Active
            </div>
            <div id="lastUpdated" style="font-size: 0.65rem; color: var(--text-dim); margin-bottom: 0.5rem; font-family: var(--font-body); font-style: italic;">
                Last Updated: ${new Date().toLocaleTimeString()}
            </div>
            <button id="refreshDataBtn" class="pill flex items-center justify-center gap-2" style="width: 100%; font-size: 0.7rem; letter-spacing: 1px;">
                ${iconRefresh(12)} REFRESH FEED
            </button>
        </div>
    `;
}

export function renderHeader(container) {
    container.innerHTML = `
        <header class="header">
            <div class="header__search">
                <span class="icon">${iconTarget(18)}</span>
                <input type="text" placeholder="Search archives...">
            </div>
            <button id="logoutBtn" class="logout-btn">TERMINATE SESSION</button>
        </header>
    `;
    
    container.querySelector('#logoutBtn')?.addEventListener('click', () => {
        auth.logout();
        window.location.reload();
    });
}
