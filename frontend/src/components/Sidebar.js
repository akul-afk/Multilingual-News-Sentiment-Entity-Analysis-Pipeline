import { NAV_ITEMS } from '../utils/constants.js';
import { navigate } from '../router.js';
import { iconGlobe, iconLive } from '../utils/icons.js';

export function renderSidebar(container) {
  const el = document.createElement('aside');
  el.className = 'sidebar';
  el.innerHTML = `
    <div class="sidebar__logo">
      <div class="sidebar__logo-icon">${iconGlobe(22, '#58A6FF')}</div>
      <div>
        <div class="sidebar__logo-text">Global News Pulse</div>
        <div class="sidebar__logo-sub">Intelligence Suite</div>
      </div>
    </div>
    <nav class="sidebar__nav">
      ${NAV_ITEMS.map(item => `
        <button class="sidebar__link" data-hash="${item.hash}">
          <span class="sidebar__link-icon">${item.icon}</span>
          <span>${item.label}</span>
        </button>
      `).join('')}
    </nav>
    <div class="sidebar__footer">
      <div class="sidebar__status">
        ${iconLive(8)}
        <span>Pipeline Active</span>
      </div>
    </div>
  `;

  el.querySelectorAll('.sidebar__link').forEach(link => {
    link.addEventListener('click', () => {
      navigate(link.dataset.hash);
    });
  });

  container.appendChild(el);
  return el;
}
