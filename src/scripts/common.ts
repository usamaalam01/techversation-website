// Runs on every page: theme switch, mobile menu, toast. Progress helpers are shared with the page scripts.
export function getDone(slug: string): string[] {
  try { return JSON.parse(localStorage.getItem('tv-done-' + slug) || '[]'); } catch { return []; }
}
export function setDone(slug: string, list: string[]) {
  try { localStorage.setItem('tv-done-' + slug, JSON.stringify(list)); } catch { /* private mode */ }
}
export function toast(msg: string) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout((toast as any).h);
  (toast as any).h = setTimeout(() => t.classList.remove('show'), 3200);
}

function paintTheme() {
  const now = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  document.querySelectorAll<HTMLButtonElement>('[data-theme-set]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.themeSet === now)));
}
document.querySelectorAll<HTMLButtonElement>('[data-theme-set]').forEach((b) =>
  b.addEventListener('click', () => {
    const t = b.dataset.themeSet === 'dark' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', t);
    try { localStorage.setItem('tv-theme', t); } catch { /* private mode */ }
    paintTheme();
  }),
);
paintTheme();

const menu = document.getElementById('menu');
const nav = document.getElementById('nav');
menu?.addEventListener('click', () => {
  const open = nav!.classList.toggle('open');
  menu.setAttribute('aria-expanded', String(open));
});
