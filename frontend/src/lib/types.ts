// These shapes match what the server sends (see docs/CONTRACT.md and backend/app/state.py).

export type Severity = 'info' | 'warning' | 'critical';

export type ActuatorName = 'light' | 'growlight' | 'pump' | 'fan' | 'humidifier' | 'heater' | 'buzzer';

export interface Alert {
  id: number;
  ts: number;
  type: string;
  severity: Severity;
  message: string;
  data: Record<string, unknown>;
  acknowledged: boolean;
}

export interface Person {
  name: string;
  last_seen: number;
  present: boolean;
}

export interface CameraEvent {
  type: 'person' | 'movement' | 'fire' | 'smoke' | 'face';
  confidence: number | null;
  name: string | null;
  snapshot: string | null;
  ts: number;
}

export interface HomeSnapshot {
  env: { temp_c?: number; humidity?: number; iaq?: number; pressure_hpa?: number; ts?: number };
  soil: { id: number; moisture_pct: number }[];
  fire: { flame?: boolean; gas_level?: number };
  door: { locked: boolean | null };
  actuators: Record<ActuatorName, boolean | null>;
  armed: boolean;
  nodes: Record<string, boolean>;
  people: Person[];
  mold: { risk: boolean; building_seconds: number };
  last_camera: CameraEvent | null;
  ts: number;
}

export interface AccessEntry {
  ts: number;
  method: 'fingerprint' | 'keypad' | 'face' | 'app';
  user: string | null;
  success: boolean;
}

export interface LabResult {
  id: number;
  ts: number;
  result: 'detected' | 'not_detected' | 'inconclusive';
  target: string;
  notes: string;
  author: string;
}

export type LiveMessage = { type: 'state'; data: HomeSnapshot } | { type: 'alert'; data: Alert };
