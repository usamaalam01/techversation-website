import { getDone, setDone, toast } from './common';

type P = { part: number; id: string; thumb: string; seconds: number; title: string };
const data: { course: string; num: string; total: number; parts: P[] } = JSON.parse(document.getElementById('module-data')!.textContent!);
const mmss = (s: number) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, '0')}`;

// player: the YouTube embed (privacy-friendly domain) is created only when play is pressed
const player = document.getElementById('player')!;
let current = data.parts[0];
function load(start = 0) {
  const f = document.createElement('iframe');
  f.src = `https://www.youtube-nocookie.com/embed/${current.id}?autoplay=1&rel=0&modestbranding=1${start ? `&start=${start}` : ''}`;
  f.title = 'YouTube video player';
  f.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
  f.allowFullscreen = true;
  player.replaceChildren(f);
}
function reset() {
  player.innerHTML = `${current.thumb ? `<img src="${current.thumb}" alt="" width="480" height="270" id="poster">` : ''}<a class="play" id="play" href="https://www.youtube.com/watch?v=${current.id}" target="_blank" rel="noopener" aria-label="Play the video"><span class="pbtn"><svg width="30" height="30" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5.5v13a1 1 0 0 0 1.5.86l10.5-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5Z"/></svg></span></a><div class="cap"><span class="dur">${mmss(current.seconds)}</span></div>`;
  bind();
}
function bind() {
  document.getElementById('play')?.addEventListener('click', (e) => { e.preventDefault(); load(); });
}
bind();

// parts: the video, the transcript and the chapters follow the selected part
document.querySelectorAll<HTMLButtonElement>('.part').forEach((b) =>
  b.addEventListener('click', () => {
    const n = Number(b.dataset.part);
    current = data.parts.find((p) => p.part === n)!;
    document.querySelectorAll('.part').forEach((x) => x.setAttribute('aria-selected', String(x === b)));
    document.querySelectorAll<HTMLElement>('.transcript, .chapters').forEach((el) => (el.hidden = Number(el.dataset.part) !== n));
    reset();
  }),
);
document.querySelectorAll<HTMLButtonElement>('.chap').forEach((b) => b.addEventListener('click', () => { load(Number(b.dataset.t)); player.scrollIntoView({ behavior: 'smooth', block: 'center' }); }));

// tabs
const tabs = Array.from(document.querySelectorAll<HTMLButtonElement>('#mtabs .tab'));
function show(tab: string) {
  tabs.forEach((t) => t.setAttribute('aria-selected', String(t.dataset.tab === tab)));
  document.querySelectorAll<HTMLElement>('.tabpanel').forEach((p) => (p.hidden = p.id !== 'p-' + tab));
}
tabs.forEach((t) => t.addEventListener('click', () => show(t.dataset.tab!)));

// progress, saved in this browser
const btn = document.getElementById('done') as HTMLButtonElement;
const check = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>';
function paint() {
  const done = getDone(data.course);
  const on = done.includes(data.num);
  btn.setAttribute('aria-pressed', String(on));
  btn.className = 'btn ' + (on ? 'btn-primary' : 'btn-ghost');
  btn.innerHTML = on ? `${check} Done` : 'Mark as done';
  document.getElementById('side-count')!.textContent = `${done.length} / ${data.total}`;
  document.querySelectorAll<HTMLElement>('.side-item').forEach((a) => {
    const ck = a.querySelector('.ck') as HTMLElement;
    const d = done.includes(a.dataset.num!);
    ck.className = 'ck' + (d ? ' on' : '');
    ck.innerHTML = d ? check.replace('width="18" height="18"', 'width="11" height="11"') : '';
  });
}
btn.addEventListener('click', () => {
  const done = getDone(data.course);
  const k = done.indexOf(data.num);
  if (k >= 0) done.splice(k, 1); else done.push(data.num);
  setDone(data.course, done);
  paint();
  toast(k >= 0 ? 'Marked as not done.' : 'Marked as done. Progress is saved in this browser.');
});
paint();
const cur = document.querySelector<HTMLElement>('.side-item[aria-current="page"]');
const list = document.getElementById('side-list')!;
if (cur) list.scrollTop = Math.max(0, cur.offsetTop - 120);
