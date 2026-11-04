// Site data, read from the files that tools/export_content.py writes. Nothing here is typed by hand.
import site from '../data/site.json';
import channel from '../data/channel.json';

export type Part = { part: number; id: string; title: string; seconds: number | null; chapters: [number, string][]; published?: string; thumb: string | null };
export type Module = { num: string; slug: string; title: string; desc: string; parts: Part[]; deck: string | null; deck_kb: number | null; seconds: number; words: number };
export type NoteMeta = { num: string; slug: string; title: string; group: string; los: string[]; minutes: number; domain: string; module: string | null; modules: string[]; tasks: number; tn: string; ref: string; of: number };
export type Course = {
  slug: string; institute: string; short: string; name: string; title: string; accent: string; desc: string; audience: string; sources: string;
  kind: string; topic: string | null; playlist: string; cover: string; modules: Module[]; facts: { questions: string; time: string; passing: string; source: string; url: string } | null;
  videos: number; seconds: number; notes: NoteMeta[] | null; glossary: number;
};
export type Institute = { id: string; name: string; full: string; mono: string; certs: string[]; soon?: string[]; hidden?: boolean };
export type Soon = { slug: string; institute: string | null; short: string; name: string; kind: string; desc: string };

export const institutes = site.institutes as Institute[];
export const courses = site.courses as unknown as Course[];
export const soon = site.soon as Soon[];
export const SUBSCRIBE_URL = `https://www.youtube.com/@${channel.handle.replace(/^@/, '')}?sub_confirmation=1`;
export const CHANNEL_URL = `https://www.youtube.com/@${channel.handle.replace(/^@/, '')}`;

export const BASE = import.meta.env.BASE_URL;
export const u = (p: string) => (BASE + p.replace(/^\//, '')).replace(/\/{2,}/g, '/');

export const inst = (id: string) => institutes.find((i) => i.id === id)!;
export const courseUrl = (c: Course) => u(`${c.institute}/${c.slug}/`);
export const moduleUrl = (c: Course, m: Module) => u(`${c.institute}/${c.slug}/video/${m.slug}/`);
export const notesUrl = (c: Course, n: { slug: string }) => u(`${c.institute}/${c.slug}/notes/${n.slug}/`);
export const playlistUrl = (c: Course) => `https://www.youtube.com/playlist?list=${c.playlist}`;
export const watchUrl = (id: string, t = 0) => `https://www.youtube.com/watch?v=${id}${t ? `&t=${t}s` : ''}`;

export function mmss(sec: number): string {
  sec = Math.round(sec);
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
  const two = (n: number) => String(n).padStart(2, '0');
  return h ? `${h}:${two(m)}:${two(s)}` : `${m}:${two(s)}`;
}
export function hm(sec: number): string {
  const min = Math.round(sec / 60), h = Math.floor(min / 60), m = min % 60;
  return h ? `${h} h${m ? ` ${m} min` : ''}` : `${m} min`;
}
export function iso(sec: number): string {
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = Math.round(sec % 60);
  return `PT${h ? h + 'H' : ''}${m ? m + 'M' : ''}${s}S`;
}

const transcripts = import.meta.glob('../data/transcripts/*/*.json', { eager: true, import: 'default' }) as Record<string, Record<string, { title: string; text: string; at?: number }[]>>;
const notes = import.meta.glob('../data/notes/*/*.json', { eager: true, import: 'default' }) as Record<string, any>;
const glossaries = import.meta.glob('../data/glossary/*.json', { eager: true, import: 'default' }) as Record<string, { terms: { term: string; text: string; module: string; group: string }[]; note: string }>;

export const transcript = (course: string, num: string) => transcripts[`../data/transcripts/${course}/${num}.json`] ?? {};
export const note = (course: string, num: string) => notes[`../data/notes/${course}/${num}.json`];
export const glossary = (course: string) => glossaries[`../data/glossary/${course}.json`];

export function totals() {
  return { courses: courses.length, modules: courses.reduce((a, c) => a + c.modules.length, 0), videos: courses.reduce((a, c) => a + c.videos, 0), seconds: courses.reduce((a, c) => a + c.seconds, 0) };
}
export const independence =
  'Techversation is an independent learning site. It is not affiliated with, endorsed by or sponsored by PMI, Scrum Alliance, IAPP, The Linux Foundation, the CNCF, DAMA International or The Open Group. Their names are used only to say which exam a course prepares for, and all trademarks belong to their owners. Exam details change, so check the official site before you book.';

export const certCourses = courses.filter((c) => c.kind !== 'training');
export const trainingCourses = courses.filter((c) => c.kind === 'training');
export const listedInstitutes = institutes.filter((i) => !i.hidden);
