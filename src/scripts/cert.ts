import { getDone } from './common';

const data: { slug: string; modules: { num: string; url: string }[] } = JSON.parse(document.getElementById('course-data')!.textContent!);

// tabs, with the tab name in the address so a tab can be linked
const tabs = Array.from(document.querySelectorAll<HTMLButtonElement>('#tabs .tab'));
const panels = Array.from(document.querySelectorAll<HTMLElement>('.tabpanel'));
function show(tab: string) {
  tabs.forEach((t) => t.setAttribute('aria-selected', String(t.dataset.tab === tab)));
  panels.forEach((p) => (p.hidden = p.id !== 'p-' + tab));
}
tabs.forEach((t) => t.addEventListener('click', () => { show(t.dataset.tab!); history.replaceState(null, '', '#' + t.dataset.tab); }));
const fromHash = () => { const w = location.hash.slice(1); show(tabs.some((t) => t.dataset.tab === w) ? w : 'video'); };
fromHash();
window.addEventListener('hashchange', fromHash);
document.getElementById('to-notes')?.addEventListener('click', (e) => { e.preventDefault(); show('notes'); history.replaceState(null, '', '#notes'); document.getElementById('tabs')!.scrollIntoView({ behavior: 'smooth' }); });

// progress saved in this browser: check marks, the progress bar and the main button
const done = getDone(data.slug);
document.querySelectorAll<HTMLElement>('.mod').forEach((row) => {
  if (done.includes(row.dataset.num!)) {
    const mark = row.querySelector('[data-mark]');
    if (mark) mark.outerHTML = '<span class="done-mark" title="Done"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg></span>';
  }
});
if (done.length) {
  const next = data.modules.find((m) => !done.includes(m.num)) ?? data.modules[0];
  const go = document.getElementById('go') as HTMLAnchorElement;
  go.href = next.url;
  go.innerHTML = `Continue with Module ${next.num} ${go.querySelector('svg')?.outerHTML ?? ''}`;
  (document.getElementById('bar') as HTMLElement).style.width = Math.round((done.length / data.modules.length) * 100) + '%';
  document.getElementById('pcount')!.textContent = `${done.length} of ${data.modules.length} modules done`;
}

// glossary filter
const gq = document.getElementById('gq') as HTMLInputElement | null;
gq?.addEventListener('input', () => {
  const q = gq.value.trim().toLowerCase();
  let n = 0;
  document.querySelectorAll<HTMLElement>('#gl .gloss-item').forEach((it) => {
    const hit = !q || it.dataset.q!.includes(q);
    it.hidden = !hit;
    if (hit) n++;
  });
  (document.getElementById('gl-empty') as HTMLElement).hidden = n > 0;
});

// study notes: filter and the two views (study order, exam domain)
const nq = document.getElementById('nq') as HTMLInputElement | null;
function filterNotes() {
  const q = (nq?.value ?? '').trim().toLowerCase();
  let shown = 0;
  document.querySelectorAll<HTMLElement>('#p-notes .notes-group').forEach((g) => {
    let any = false;
    g.querySelectorAll<HTMLElement>('.note-row').forEach((r) => { const hit = !q || r.dataset.q!.includes(q); r.hidden = !hit; if (hit) any = true; });
    g.hidden = !any;
    if (any && !g.closest('[hidden]')) shown += g.querySelectorAll('.note-row:not([hidden])').length;
  });
  const empty = document.getElementById('notes-empty');
  if (empty) empty.hidden = shown > 0;
}
nq?.addEventListener('input', filterNotes);
document.querySelectorAll<HTMLButtonElement>('[data-notes-view]').forEach((b) =>
  b.addEventListener('click', () => {
    const v = b.dataset.notesView;
    document.querySelectorAll('[data-notes-view]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
    (document.getElementById('notes-order') as HTMLElement).hidden = v !== 'order';
    const d = document.getElementById('notes-domain');
    if (d) d.hidden = v !== 'domain';
    filterNotes();
  }),
);
