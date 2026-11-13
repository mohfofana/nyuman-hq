export const DAY_START = 6;
export const DAY_END = 23;

export function startOfWeek(d: Date) {
  const x = new Date(d);
  const day = (x.getDay() + 6) % 7; // lundi = 0
  x.setHours(0, 0, 0, 0);
  x.setDate(x.getDate() - day);
  return x;
}
export const addDays = (d: Date, n: number) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
export const sameDay = (a: Date, b: Date) => a.toDateString() === b.toDateString();
export const hm = (d: Date | string) => new Date(d).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
export function longDate(d: Date | string) {
  const s = new Date(d).toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });
  return s.charAt(0).toUpperCase() + s.slice(1);
}
export function relativeStart(start: string, end: string): { label: string; live: boolean; past: boolean } {
  const now = Date.now(), s = new Date(start).getTime(), e = new Date(end).getTime();
  if (now >= s && now < e) return { label: "En cours", live: true, past: false };
  if (now >= e) return { label: "Terminée", live: false, past: true };
  const min = Math.round((s - now) / 60000);
  if (min < 60) return { label: `Dans ${min} min`, live: false, past: false };
  if (sameDay(new Date(start), new Date())) return { label: `Aujourd'hui à ${hm(start)}`, live: false, past: false };
  if (sameDay(new Date(start), addDays(new Date(), 1))) return { label: `Demain à ${hm(start)}`, live: false, past: false };
  return { label: `${longDate(start)} à ${hm(start)}`, live: false, past: false };
}
