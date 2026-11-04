import { getDone, toast } from './common';

type Pick = { id: string; name: string; certs: { slug: string; label: string; url: string }[]; soon: string[] };
const picker: Pick[] = JSON.parse(document.getElementById('picker-data')!.textContent!);
const fi = document.getElementById('f-inst') as HTMLSelectElement;
const fc = document.getElementById('f-cert') as HTMLSelectElement;

fi.addEventListener('change', () => {
  const i = picker.find((p) => p.id === fi.value);
  if (!i) { fc.disabled = true; fc.innerHTML = '<option value="">Pick an institute first</option>'; return; }
  fc.disabled = false;
  fc.innerHTML = i.certs.map((c) => `<option value="${c.url}">${c.label.replace(/&/g, '&amp;')}</option>`).join('') +
    i.soon.map((s) => `<option value="" disabled>${s} · coming soon</option>`).join('');
});
document.getElementById('f-go')!.addEventListener('click', () => {
  if (fc.value) location.href = fc.value;
  else toast('Choose an institute and a certification first.');
});

// "continue where you left off" on the cards, from the progress saved in this browser
const resume: { slug: string; mods: { num: string; title: string; url: string }[] }[] = JSON.parse(document.getElementById('resume-data')!.textContent!);
for (const c of resume) {
  const done = getDone(c.slug);
  const box = document.querySelector<HTMLElement>(`[data-resume="${c.slug}"]`);
  if (!box || !done.length) continue;
  const next = c.mods.find((m) => !done.includes(m.num));
  box.textContent = next ? `You have done ${done.length} of ${c.mods.length} modules. Next: Module ${next.num}.` : `You have done all ${c.mods.length} modules.`;
  box.hidden = false;
}

// the request goes to the channel owner by email; the address is assembled here so it is not sitting in the page source
document.getElementById('req')!.addEventListener('submit', (e) => {
  e.preventDefault();
  const what = (document.getElementById('r-what') as HTMLInputElement).value.trim();
  const why = (document.getElementById('r-why') as HTMLTextAreaElement).value.trim();
  const mail = (document.getElementById('r-mail') as HTMLInputElement).value.trim();
  const to = ['usamaalam', 'gmail.com'].join('@');
  const body = `Course request: ${what}\n\nWhy: ${why || '-'}\nReply to: ${mail || '-'}`;
  location.href = `mailto:${to}?subject=${encodeURIComponent('Techversation course request: ' + what)}&body=${encodeURIComponent(body)}`;
  toast('Your email app should open with the request ready to send.');
});
