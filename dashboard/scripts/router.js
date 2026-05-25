import { renderSidebar, renderHeader } from './components.js';
import { auth } from './utils/auth.js';
import { destroyAll } from './utils/chartManager.js';
import { initTornCards } from './utils/tearEffect.js';
import { loadDashboardData } from './utils/dataLoader.js';
import { iconRefresh } from './icons.js';

const routes = {};
let currentHash = null;
let appEl = null;
let contentEl = null;
let globalData = null;
let shellBuilt = false;

export function registerRoute(hash, mountFn, unmountFn) {
    routes[hash] = { mountFn, unmountFn };
}

export async function initRouter(app, data) {
    appEl = app;
    globalData = data;
    window.addEventListener('hashchange', () => handleRoute());
    handleRoute();
}

export async function reloadData(newData) {
    globalData = newData;
    handleRoute(); // Re-render current route with new data
}

function buildShell() {
    if (shellBuilt) return;
    appEl.innerHTML = '';
    appEl.className = 'app';
    
    const sidebarContainer = document.createElement('aside');
    sidebarContainer.className = 'sidebar';
    renderSidebar(sidebarContainer);
    appEl.appendChild(sidebarContainer);

    const main = document.createElement('main');
    main.className = 'main';
    renderHeader(main);
    
    contentEl = document.createElement('div');
    contentEl.className = 'content';
    main.appendChild(contentEl);
    
    appEl.appendChild(main);
    
    // Hook up refresh button
    const refreshBtn = sidebarContainer.querySelector('#refreshDataBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            refreshBtn.disabled = true;
            refreshBtn.textContent = '... SYNCING ...';
            try {
                const newData = await loadDashboardData();
                await reloadData(newData);
                const timeEl = sidebarContainer.querySelector('#lastUpdated');
                if (timeEl) timeEl.textContent = `Last Updated: ${new Date().toLocaleTimeString()}`;
            } catch (err) {
                console.error('Refresh failed:', err);
                alert('News feed synchronization failed.');
            } finally {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = `${iconRefresh(12)} REFRESH FEED`;
            }
        });
    }

    shellBuilt = true;
}

async function handleRoute() {
    const hash = window.location.hash || '#landing';
    
    // Auth Guard
    if (!auth.isAuthenticated() && hash !== '#login' && hash !== '#landing') {
        window.location.hash = '#landing';
        return;
    }

    if (hash === '#login' && auth.isAuthenticated()) {
        window.location.hash = '#overview';
        return;
    }

    const route = routes[hash];
    if (!route) return;

    // Cleanup previous
    if (currentHash && routes[currentHash]?.unmountFn) {
        routes[currentHash].unmountFn();
    }
    destroyAll(); // Global chart cleanup

    if (hash === '#login' || hash === '#landing') {
        shellBuilt = false;
        appEl.innerHTML = '';
        route.mountFn(appEl, () => {
            window.location.hash = '#overview';
            window.location.reload(); // Refresh to build shell
        });
    } else {
        buildShell();
        updateActiveLink(hash);
        contentEl.innerHTML = '<div class="loading-spinner"></div>';
        setTimeout(() => {
            contentEl.innerHTML = '';
            route.mountFn(contentEl, globalData);
            // Initialize torn edge effect on new content
            setTimeout(() => initTornCards(), 100);
        }, 300);
    }
    
    currentHash = hash;
}

function updateActiveLink(hash) {
    document.querySelectorAll('.sidebar__link').forEach(link => {
        link.classList.toggle('sidebar__link--active', link.getAttribute('href') === hash);
    });
}
