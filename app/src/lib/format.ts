export function timeAgo(tsSeconds: number, nowMs: number = Date.now()): string {
  const s = Math.max(0, Math.round(nowMs / 1000 - tsSeconds));
  if (s < 10) return 'just now';
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return `${Math.floor(s / 86400)} d ago`;
}

export function num(value: number | undefined | null, digits = 0): string {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : '–';
}

export const ALERT_TITLE: Record<string, string> = {
  mold_risk: 'Mold risk',
  fire: 'Fire',
  intrusion: 'Intruder',
  unknown_person: 'Unknown person',
  plant_dry: 'Thirsty plant',
  door_failed_attempts: 'Door attempts',
  node_offline: 'Board offline',
};
