// notes page: table of contents highlight, "show the answer" reveal, and the list of all notes (open beside the note on wide screens)
const heads = Array.from(document.querySelectorAll<HTMLElement>('.note-sec'));
const links = Array.from(document.querySelectorAll<HTMLAnchorElement>('.toc a'));
if ('IntersectionObserver' in window) {
  const io = new IntersectionObserver(
    (es) => es.forEach((e) => { if (e.isIntersecting) links.forEach((a) => a.classList.toggle('on', a.getAttribute('href') === '#' + e.target.id)); }),
    { rootMargin: '-20% 0px -70% 0px' },
  );
  heads.forEach((h) => io.observe(h));
}
document.querySelectorAll<HTMLDetailsElement>('.qa details').forEach((d) =>
  d.addEventListener('toggle', () => d.closest('.qa')!.classList.toggle('revealed', d.open)),
);

// review checklists keep their ticks in this browser
const page = location.pathname;
document.querySelectorAll<HTMLInputElement>('.note-sec li.task input[data-task]').forEach((box, i) => {
  const key = 'tv-task-' + page + '-' + i;
  try { if (localStorage.getItem(key) === '1') { box.checked = true; box.closest('li')!.classList.add('done'); } } catch { /* private mode */ }
  box.addEventListener('change', () => {
    box.closest('li')!.classList.toggle('done', box.checked);
    try { localStorage.setItem(key, box.checked ? '1' : '0'); } catch { /* private mode */ }
  });
});

const nav = document.getElementById('notes-nav') as HTMLDetailsElement | null;
if (nav) {
  nav.open = window.matchMedia('(min-width: 1180px)').matches;
  const cur = nav.querySelector<HTMLElement>('[aria-current="page"]');
  const box = nav.querySelector<HTMLElement>('nav');
  if (cur && box && nav.open) box.scrollTop = Math.max(0, cur.offsetTop - box.clientHeight / 3);
}
