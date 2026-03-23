import { COLORS, ENTITY_STYLES } from '../utils/constants.js';
import { compactNumber } from '../utils/formatters.js';

export function renderEntities(container, data) {
  const entities = data.entities?.entities || [];
  const coOccurrence = data.entities?.co_occurrence || [];

  // Group entities by label
  const byLabel = {};
  entities.forEach(e => {
    if (!byLabel[e.label]) byLabel[e.label] = [];
    byLabel[e.label].push(e);
  });

  const totalCount = entities.reduce((s, e) => s + e.count, 0);
  const selectedEntity = entities[0] || { name: 'N/A', label: 'N/A', count: 0, sources: {} };

  // Filter type pills
  const labels = ['All', ...Object.keys(byLabel)];

  const el = document.createElement('div');
  el.innerHTML = `
    <div class="page-title">
      <h1>Entity Explorer</h1>
      <p>Named entity analysis across all news sources — People, Organizations, Locations</p>
    </div>

    <!-- Filter Bar -->
    <div class="pills" style="margin-bottom: var(--space-6); display: inline-flex">
      ${labels.map((l, i) => `
        <button class="pill ${i === 0 ? 'pill--active' : ''}" data-label="${l}">${l}</button>
      `).join('')}
    </div>

    <div class="grid grid--65-35">
      <div>
        <!-- Treemap -->
        <div class="card" style="margin-bottom: var(--space-6)">
          <div class="card__header">
            <span class="card__title">Entity Volume Treemap</span>
          </div>
          <div class="treemap" id="entity-treemap" style="grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); grid-auto-rows: minmax(60px, auto)">
          </div>
        </div>

        <!-- Co-occurrence Network -->
        <div class="card">
          <div class="card__header">
            <span class="card__title">Entity Co-occurrence Network</span>
            <span class="text-dim" style="font-size: 0.8rem">${coOccurrence.length} connections</span>
          </div>
          <canvas id="network-canvas" class="network-canvas" width="700" height="300"></canvas>
        </div>
      </div>

      <!-- Entity Detail Card -->
      <div>
        <div class="card" id="entity-detail-card">
          <div class="card__header">
            <span class="card__title">Entity Details</span>
          </div>
          <h2 style="font-size: 1.5rem; margin-bottom: var(--space-2)">${selectedEntity.name}</h2>
          <span class="entity-tag ${(ENTITY_STYLES[selectedEntity.label]?.className || 'entity-tag--other')}">${selectedEntity.label}</span>
          <div style="margin-top: var(--space-6)">
            <div class="stat-row">
              <span class="stat-row__label">Total Mentions</span>
              <span class="stat-row__value">${selectedEntity.count}</span>
            </div>
            <div class="stat-row">
              <span class="stat-row__label">Share of All</span>
              <span class="stat-row__value">${totalCount ? Math.round(selectedEntity.count / totalCount * 100) : 0}%</span>
            </div>
          </div>
          <h4 style="margin-top: var(--space-5); margin-bottom: var(--space-3); font-size: 0.85rem; color: var(--text-muted)">Source Breakdown</h4>
          ${Object.entries(selectedEntity.sources || {}).map(([src, count]) => `
            <div class="stat-row">
              <span class="stat-row__label">${src.replace('BBC ', '')}</span>
              <span class="stat-row__value">${count}</span>
            </div>
          `).join('')}
        </div>

        <!-- Top by Category -->
        <div class="card" style="margin-top: var(--space-6)">
          <div class="card__header">
            <span class="card__title">Top by Category</span>
          </div>
          ${Object.entries(byLabel).slice(0, 4).map(([label, items]) => `
            <div style="margin-bottom: var(--space-4)">
              <div style="font-size: 0.75rem; font-weight: 600; color: var(--text-dim); margin-bottom: var(--space-2)">${label}</div>
              <div>
                ${items.slice(0, 5).map(e => `
                  <span class="entity-tag ${(ENTITY_STYLES[e.label]?.className || 'entity-tag--other')}" style="margin: 2px">${e.name} (${e.count})</span>
                `).join('')}
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;

  container.appendChild(el);

  // ── Render Treemap ──
  const treemap = document.getElementById('entity-treemap');
  const maxCount = entities[0]?.count || 1;

  entities.slice(0, 25).forEach(e => {
    const size = Math.max(60, Math.sqrt(e.count / maxCount) * 160);
    const color = ENTITY_STYLES[e.label]?.color || COLORS.textDim;
    const cell = document.createElement('div');
    cell.className = 'treemap__cell';
    cell.style.cssText = `background: ${color}22; border-left: 3px solid ${color}; min-height: ${size}px;`;
    cell.innerHTML = `
      <span class="treemap__cell-label">${e.label}</span>
      <span class="treemap__cell-name">${e.name}</span>
      <span class="treemap__cell-count">${e.count} mentions</span>
    `;
    cell.addEventListener('click', () => updateDetail(e));
    treemap.appendChild(cell);
  });

  // ── Update detail card on click ──
  function updateDetail(entity) {
    const card = document.getElementById('entity-detail-card');
    card.querySelector('h2').textContent = entity.name;
    card.querySelector('.entity-tag').textContent = entity.label;
    card.querySelector('.entity-tag').className = `entity-tag ${ENTITY_STYLES[entity.label]?.className || 'entity-tag--other'}`;
    const statValues = card.querySelectorAll('.stat-row__value');
    if (statValues[0]) statValues[0].textContent = entity.count;
    if (statValues[1]) statValues[1].textContent = totalCount ? Math.round(entity.count / totalCount * 100) + '%' : '0%';
  }

  // ── Filter pills ──
  el.querySelectorAll('.pill').forEach(pill => {
    pill.addEventListener('click', () => {
      el.querySelectorAll('.pill').forEach(p => p.classList.remove('pill--active'));
      pill.classList.add('pill--active');
      const label = pill.dataset.label;
      const filtered = label === 'All' ? entities : entities.filter(e => e.label === label);
      treemap.innerHTML = '';
      const filteredMax = filtered[0]?.count || 1;
      filtered.slice(0, 25).forEach(e => {
        const size = Math.max(60, Math.sqrt(e.count / filteredMax) * 160);
        const color = ENTITY_STYLES[e.label]?.color || COLORS.textDim;
        const cell = document.createElement('div');
        cell.className = 'treemap__cell';
        cell.style.cssText = `background: ${color}22; border-left: 3px solid ${color}; min-height: ${size}px;`;
        cell.innerHTML = `<span class="treemap__cell-label">${e.label}</span><span class="treemap__cell-name">${e.name}</span><span class="treemap__cell-count">${e.count} mentions</span>`;
        cell.addEventListener('click', () => updateDetail(e));
        treemap.appendChild(cell);
      });
    });
  });

  // ── Co-occurrence Network (Canvas) ──
  const canvas = document.getElementById('network-canvas');
  if (canvas && coOccurrence.length) {
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    const nodes = {};
    coOccurrence.forEach(({ source, target }) => {
      if (!nodes[source]) nodes[source] = { x: Math.random() * (w - 100) + 50, y: Math.random() * (h - 60) + 30 };
      if (!nodes[target]) nodes[target] = { x: Math.random() * (w - 100) + 50, y: Math.random() * (h - 60) + 30 };
    });

    // Draw edges
    coOccurrence.slice(0, 20).forEach(({ source, target, weight }) => {
      const a = nodes[source], b = nodes[target];
      if (!a || !b) return;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.strokeStyle = `rgba(88, 166, 255, ${Math.min(weight / 10, 0.5)})`;
      ctx.lineWidth = Math.max(1, weight / 3);
      ctx.stroke();
    });

    // Draw nodes
    Object.entries(nodes).forEach(([name, pos]) => {
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 6, 0, Math.PI * 2);
      ctx.fillStyle = COLORS.primary;
      ctx.fill();
      ctx.fillStyle = COLORS.textMuted;
      ctx.font = '10px Inter';
      ctx.textAlign = 'center';
      ctx.fillText(name.slice(0, 12), pos.x, pos.y - 10);
    });
  }
}
