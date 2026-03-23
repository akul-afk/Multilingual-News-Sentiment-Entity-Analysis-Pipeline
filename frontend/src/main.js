/**
 * Global News Pulse — Main Entry Point
 * Loads data, initializes layout, and starts the router.
 */

import './styles/index.css';
import './styles/layout.css';
import './styles/components.css';
import './styles/charts.css';

import { loadData } from './utils/dataLoader.js';
import { registerRoute, initRouter } from './router.js';
import { renderSidebar } from './components/Sidebar.js';
import { renderHeader } from './components/Header.js';

import { renderOverview } from './screens/Overview.js';
import { renderSentiment } from './screens/SentimentAnalysis.js';
import { renderEntities } from './screens/EntityExplorer.js';
import { renderReports } from './screens/Reports.js';
import { renderHeatmap } from './screens/GeoHeatmap.js';

async function init() {
  const app = document.getElementById('app');

  // Show loading state
  app.innerHTML = `
    <div class="loading">
      <div class="loading__spinner"></div>
      <p class="text-muted">Loading Global News Pulse...</p>
    </div>
  `;

  try {
    // Load dashboard data
    const data = await loadData();

    // Build app shell
    app.innerHTML = '';
    app.className = 'app';

    // Sidebar
    renderSidebar(app);

    // Main area
    const main = document.createElement('main');
    main.className = 'main';

    // Header
    renderHeader(main);

    // Content area (screens render here)
    const content = document.createElement('div');
    content.className = 'content';
    content.id = 'screen-content';
    main.appendChild(content);

    app.appendChild(main);

    // Register routes
    registerRoute('#overview', renderOverview);
    registerRoute('#sentiment', renderSentiment);
    registerRoute('#entities', renderEntities);
    registerRoute('#reports', renderReports);
    registerRoute('#heatmap', renderHeatmap);

    // Start router
    initRouter(content, data);

  } catch (err) {
    console.error('Failed to initialize:', err);
    app.innerHTML = `
      <div class="loading">
        <p style="color: var(--error)">❌ Failed to load dashboard data</p>
        <p class="text-dim">${err.message}</p>
        <p class="text-dim" style="margin-top: 1rem">Make sure <code>data/dashboard_data.json</code> exists in the public folder.</p>
      </div>
    `;
  }
}

// Boot
init();
