import { initRouter, registerRoute } from './router.js';
import { loadDashboardData } from './utils/dataLoader.js';

// Screens
import { mountLogin, unmountLogin } from './screens/Login.js';
import { mountOverview, unmountOverview } from './screens/Overview.js';
import { mountSentiment, unmountSentiment } from './screens/Sentiment.js';
import { mountCrossLanguage, unmountCrossLanguage } from './screens/CrossLanguage.js';
import { mountEntityExplorer, unmountEntityExplorer } from './screens/EntityExplorer.js';
import { mountGeoHeatmap, unmountGeoHeatmap } from './screens/GeoHeatmap.js';
import { mountReports, unmountReports } from './screens/Reports.js';
import { mountLanding, unmountLanding } from './screens/Landing.js';

async function boot() {
    try {
        const data = await loadDashboardData();
        
        // Register all routes
        registerRoute('#login', mountLogin, unmountLogin);
        registerRoute('#landing', mountLanding, unmountLanding);
        registerRoute('#overview', mountOverview, unmountOverview);
        registerRoute('#sentiment', mountSentiment, unmountSentiment);
        registerRoute('#cross', mountCrossLanguage, unmountCrossLanguage);
        registerRoute('#entities', mountEntityExplorer, unmountEntityExplorer);
        registerRoute('#geo', mountGeoHeatmap, unmountGeoHeatmap);
        registerRoute('#reports', mountReports, unmountReports);

        const app = document.getElementById('app');
        await initRouter(app, data);

        // Phase 3: Dynamic Data Ingestion (Background Polling)
        setInterval(async () => {
            try {
                const { reloadData } = await import('./router.js');
                const newData = await loadDashboardData();
                reloadData(newData);
                
                // Update timestamp if sidebar exists
                const timeEl = document.getElementById('lastUpdated');
                if (timeEl) timeEl.textContent = `Last Updated: ${new Date().toLocaleTimeString()}`;
                
                console.log('Background Sync: Data ingestion complete.');
            } catch (err) {
                console.warn('Background Sync Warning:', err);
            }
        }, 30000); // Poll every 30 seconds

    } catch (err) {
        console.error('System Failure:', err);
        document.body.innerHTML = `
            <div class="system-error">
                <h1>CRITICAL SYSTEM FAILURE</h1>
                <p>Database connection lost or intelligence briefing corrupted.</p>
                <pre>${err.stack}</pre>
                <button onclick="window.location.reload()">RETRY CONNECTION</button>
            </div>
        `;
    }
}

// Global Chart.js Defaults
if (window.Chart) {
    Chart.defaults.font.family = "'IM Fell English', serif";
    Chart.defaults.color = '#5a3c1e';
}

boot();
