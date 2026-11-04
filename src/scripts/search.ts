// Full-text search over the built site with Pagefind. The index is made after the build (npm run build), so it is missing in `astro dev`.
const cfg: { base: string } = JSON.parse(document.getElementById('search-data')!.textContent!);
const q = document.getElementById('q') as HTMLInputElement;
const count = document.getElementById('count')!;
const results = document.getElementById('results')!;
const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!);

let pf: any = null;
async function engine() {
  if (pf) return pf;
  try {
    // the file only exists after the build, so it is imported at run time and the bundler is kept out of it
    pf = await new Function('u', 'return import(u)')(`${cfg.base}pagefind/pagefind.js`);
    await pf.options({ baseUrl: cfg.base });
    await pf.init();
  } catch (err) {
    console.error('Pagefind could not start', err);
    pf = false;
  }
  return pf;
}

function checked(sel: string, attr: string): string[] {
  return Array.from(document.querySelectorAll<HTMLInputElement>(`${sel} input:checked`)).map((i) => i.dataset[attr]!);
}
let ticket = 0;
async function run() {
  const my = ++ticket;
  const term = q.value.trim();
  const e = await engine();
  if (e === false) { count.textContent = 'Search is built with the site. Run "npm run build" and open the built site.'; results.innerHTML = ''; return; }
  if (!term) { count.textContent = 'Type to search.'; results.innerHTML = ''; return; }
  const inst = checked('#f-inst', 'inst'), types = checked('#f-type', 'type');
  const found = await e.search(term);
  const all: any[] = await Promise.all(found.results.slice(0, 300).map((r: any) => r.data()));
  if (my !== ticket) return;
  const first = (v: any) => (Array.isArray(v) ? v[0] : v) ?? '';
  // the counts next to the filters come from the whole result list; the list itself follows the ticked boxes
  const tally = (key: string) => all.reduce((m: Record<string, number>, d) => { const k = String(first(d.filters?.[key])); m[k] = (m[k] ?? 0) + 1; return m; }, {});
  const ci = tally('institute'), ct = tally('type');
  document.querySelectorAll<HTMLElement>('#f-inst label').forEach((l) => { l.querySelector('em')!.textContent = String(ci[l.querySelector('input')!.dataset.inst!] ?? 0); });
  document.querySelectorAll<HTMLElement>('#f-type label').forEach((l) => { l.querySelector('em')!.textContent = String(ct[l.querySelector('input')!.dataset.type!] ?? 0); });
  const shown = all.filter((d) => inst.includes(String(first(d.filters?.institute))) && types.includes(String(first(d.filters?.type))));
  const items = shown.slice(0, 40);
  count.textContent = `${shown.length} result${shown.length === 1 ? '' : 's'} for "${term}"`;
  results.innerHTML = items.map((d: any) => {
    const type = d.filters?.type?.[0] ?? d.filters?.type ?? 'Page';
    const where = d.filters?.institute?.[0] ?? d.filters?.institute ?? '';
    const img = d.meta?.image;
    return `<a class="result" href="${d.url}"><div class="rt">${img ? `<img src="${img}" alt="" loading="lazy">` : ''}</div><div><div class="where"><span class="badge accent">${esc(String(type))}</span><span>${esc(String(where))}</span></div><h3>${esc(d.meta?.title ?? d.url)}</h3><p>${d.excerpt}</p></div></a>`;
  }).join('') || '<div class="empty"><b>No results</b><span>Try a shorter word, or clear a filter. You can also <a href="' + cfg.base + '#request">request a course</a>.</span></div>';
}
q.value = new URLSearchParams(location.search).get('q') ?? '';
q.addEventListener('input', run);
document.getElementById('sform')!.addEventListener('submit', (e) => { e.preventDefault(); run(); });
document.querySelectorAll('.filters input').forEach((i) => i.addEventListener('change', run));
run();
