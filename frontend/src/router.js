/**
 * Hash-based SPA Router with smooth transitions
 */

const routes = {};
let currentRoute = null;
let contentEl = null;
let globalData = null;

export function registerRoute(hash, renderFn) {
  routes[hash] = renderFn;
}

export function navigate(hash) {
  window.location.hash = hash;
}

export function initRouter(content, data) {
  contentEl = content;
  globalData = data;

  window.addEventListener('hashchange', () => handleRoute());

  if (!window.location.hash || !routes[window.location.hash]) {
    window.location.hash = '#overview';
  } else {
    handleRoute();
  }
}

function handleRoute() {
  const hash = window.location.hash || '#overview';
  const renderFn = routes[hash];
  if (!renderFn || !contentEl) return;

  // Update sidebar active state
  document.querySelectorAll('.sidebar__link').forEach(link => {
    link.classList.toggle('sidebar__link--active', link.dataset.hash === hash);
  });

  // Smooth transition: fade out, swap, fade in
  if (currentRoute !== hash) {
    contentEl.style.transition = 'opacity 150ms ease, transform 150ms ease';
    contentEl.style.opacity = '0';
    contentEl.style.transform = 'translateY(6px)';

    setTimeout(() => {
      contentEl.innerHTML = '';
      renderFn(contentEl, globalData);
      currentRoute = hash;

      // Reset and fade in
      requestAnimationFrame(() => {
        contentEl.style.transition = 'opacity 350ms cubic-bezier(0.16, 1, 0.3, 1), transform 350ms cubic-bezier(0.16, 1, 0.3, 1)';
        contentEl.style.opacity = '1';
        contentEl.style.transform = 'translateY(0)';
      });
    }, 160);
  }
}
