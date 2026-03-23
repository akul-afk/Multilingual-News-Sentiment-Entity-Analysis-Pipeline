import { iconSearch, iconBell } from '../utils/icons.js';

export function renderHeader(container) {
  const now = new Date();
  const greeting = now.getHours() < 12 ? 'Good Morning' : now.getHours() < 17 ? 'Good Afternoon' : 'Good Evening';
  const dateStr = now.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

  const el = document.createElement('header');
  el.className = 'header';
  el.innerHTML = `
    <div class="header__greeting">
      <h2>${greeting}</h2>
      <p>${dateStr}</p>
    </div>
    <div class="header__actions">
      <div class="header__search">
        <span style="display:flex">${iconSearch(16, 'var(--text-dim)')}</span>
        <input type="text" placeholder="Search headlines..." id="global-search">
      </div>
      <span style="cursor:pointer; display:flex">${iconBell(20, 'var(--text-muted)')}</span>
    </div>
  `;

  container.appendChild(el);
  return el;
}
