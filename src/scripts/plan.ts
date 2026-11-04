type Mod = { num: string; title: string; videoMin: number; notesMin: number };
type Plan = { slug: string; short: string; name: string; hasNotes: boolean; modules: Mod[]; notesTotal: number };
const data: Plan[] = JSON.parse(document.getElementById('plan-data')!.textContent!);
const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const sel = $<HTMLSelectElement>('pc'), date = $<HTMLInputElement>('pd'), hours = $<HTMLInputElement>('ph'), notesBox = $<HTMLInputElement>('pn');
const wanted = new URLSearchParams(location.search).get('c');
if (wanted && data.some((p) => p.slug === wanted)) sel.value = wanted;

const DAY = 864e5;
const iso = (x: Date) => `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, '0')}-${String(x.getDate()).padStart(2, '0')}`;
const fmt = (x: Date) => x.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!);
const today = new Date(); today.setHours(0, 0, 0, 0);
date.min = iso(new Date(today.getTime() + DAY));
date.value = iso(new Date(today.getTime() + 42 * DAY));

function render() {
  const p = data.find((x) => x.slug === sel.value)!;
  const hrs = Number(hours.value), cap = hrs * 60;
  const withNotes = notesBox.checked && p.hasNotes;
  $('ph-out').textContent = `${hrs} h per week`;
  notesBox.disabled = !p.hasNotes;
  const exam = new Date(date.value + 'T00:00:00');
  if (isNaN(exam.getTime())) { $('plan-out').innerHTML = '<div class="alert">Choose your exam date.</div>'; return; }
  const days = Math.max(1, Math.round((exam.getTime() - today.getTime()) / DAY));
  const weeks = Math.max(1, Math.ceil(days / 7));
  const notesAvg = p.notesTotal / p.modules.length;
  // each module: its video, its study note (when the course has notes) and 10 minutes of review
  const units = p.modules.map((m) => {
    const notes = withNotes ? (m.notesMin || Math.round(notesAvg)) : 0;
    return { title: `Module ${m.num}: ${m.title}`, v: m.videoMin, n: notes, mins: m.videoMin + notes + 10 };
  });
  const total = units.reduce((a, u) => a + u.mins, 0);
  const studyWeeks = weeks > 1 ? weeks - 1 : 1;
  const per = Math.min(cap, total / studyWeeks);          // spread the work evenly instead of front-loading it
  const rows: { w: number; items: typeof units; used: number }[] = [];
  let k = 0;
  for (let w = 0; w < studyWeeks; w++) {
    let used = 0; const items: typeof units = []; const last = w === studyWeeks - 1;
    while (k < units.length && (items.length === 0 || (last ? used + units[k].mins <= cap : used + units[k].mins <= cap && used + units[k].mins / 2 <= per))) { items.push(units[k]); used += units[k].mins; k++; }
    rows.push({ w, items, used });
  }
  const left = units.length - k, need = Math.ceil(total / studyWeeks / 6) / 10;
  let h = '';
  if (left > 0) h += `<div class="alert"><b>This is tight.</b> At ${hrs} hours a week, ${left} module${left > 1 ? 's do' : ' does'} not fit before the exam. You need about ${need} hours a week, or a later exam date.</div>`;
  h += `<div class="sum"><div><small>Total study time</small><b>${(total / 60).toFixed(1)} h</b></div><div><small>Weeks to exam</small><b>${weeks}</b></div><div><small>Hours per week</small><b>${hrs} h</b></div><div><small>Modules</small><b>${p.modules.length}</b></div></div><div class="weeks">`;
  for (const r of rows) {
    const s = new Date(today.getTime() + r.w * 7 * DAY), e = new Date(Math.min(s.getTime() + 6 * DAY, exam.getTime()));
    h += `<div class="week"><div class="wk"><b>Week ${r.w + 1}</b><small>${fmt(s)} to ${fmt(e)}</small></div><ul>` +
      (r.items.length ? r.items.map((u) => `<li><span style="color:var(--fg-2);font-family:var(--font-body)">${esc(u.title)}</span><span>${u.v} min video${u.n ? ` + ${u.n} min notes` : ''}</span></li>`).join('') : '<li>Buffer week: rewatch the modules you found hardest</li>') +
      `</ul><div class="hrs">${r.items.length ? (r.used / 60).toFixed(1) + ' h' : 'Buffer'}</div></div>`;
  }
  if (weeks > 1) {
    const s2 = new Date(today.getTime() + studyWeeks * 7 * DAY);
    h += `<div class="week final"><div class="wk"><b>Final week</b><small>${fmt(s2)} to ${fmt(exam)}</small></div><ul><li>Rewatch your weakest modules</li><li>Work through the quick-reference recap and the final check</li><li>Rest the day before the exam</li></ul><div class="hrs">Review</div></div>`;
  }
  $('plan-out').innerHTML = h + '</div>';
  $('plan-note').textContent = `Estimates use each video's real length, ${withNotes ? 'the reading time of each study note and ' : ''}10 minutes of review per module.`;
}
document.querySelectorAll('#plan-form input, #plan-form select').forEach((el) => { el.addEventListener('input', render); el.addEventListener('change', render); });
$('print').addEventListener('click', () => window.print());
render();
