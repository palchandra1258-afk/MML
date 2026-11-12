import type { ReactNode } from "react";

const paths: Record<string, ReactNode> = {
  overview: <><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></>,
  book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21z"/><path d="M4 5.5v13A2.5 2.5 0 0 1 6.5 16H20M8 7h8"/></>,
  progress: <><path d="M4 19V5M4 19h17"/><path d="m7 15 4-4 3 2 6-7"/><circle cx="20" cy="6" r="1.5"/></>,
  trajectory: <><circle cx="5" cy="6" r="2"/><circle cx="19" cy="18" r="2"/><path d="M7 6h5a3 3 0 0 1 3 3v3a3 3 0 0 0 3 3h1M5 8v8a2 2 0 0 0 2 2h10"/></>,
  state: <><path d="M4 19V5m0 14h16"/><path d="M7 15c2-5 3 2 5-3s3 3 6-5"/><circle cx="18" cy="7" r="1.5"/></>,
  mind: <><path d="M9 4a3 3 0 0 0-5 2 3 3 0 0 0 0 5 3 3 0 0 0 1 5 3 3 0 0 0 5 3z"/><path d="M15 4a3 3 0 0 1 5 2 3 3 0 0 1 0 5 3 3 0 0 1-1 5 3 3 0 0 1-5 3zM12 4v16m-3-9h3m3 3h-3"/></>,
  layers: <><path d="m12 3 9 5-9 5-9-5z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/></>,
  evidence: <><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5M8 10.5h5M10.5 8v5"/></>,
  research: <><path d="M5 20V8m7 12V4m7 16v-9"/><path d="M3 20h18"/></>,
  chart: <><path d="M4 19V5m0 14h16"/><path d="m7 15 4-5 3 2 5-7"/></>,
  system: <><circle cx="12" cy="12" r="8.5"/><path d="m8 12 2.5 2.5L16 9"/></>,
};

export function NavIcon({ name, size = 18 }: { name: string; size?: number }) {
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name] ?? paths.overview}</svg>;
}
