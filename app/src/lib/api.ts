import type { AccessEntry, ActuatorName, Alert, HomeSnapshot, LabResult } from './types';

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

const TIMEOUT_MS = 8000;

export function cleanBaseUrl(url: string): string {
  return url.trim().replace(/\/+$/, '');
}

export function createApi(baseUrl: string, token: string) {
  const base = cleanBaseUrl(baseUrl);

  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
    try {
      const res = await fetch(base + path, {
        ...init,
        signal: controller.signal,
        headers: {
          Authorization: `Bearer ${token}`,
          ...(init.body ? { 'Content-Type': 'application/json' } : {}),
        },
      });
      if (!res.ok) {
        let detail = '';
        try {
          const body = await res.json();
          detail = typeof body.detail === 'string' ? body.detail : '';
        } catch {
          // no readable body
        }
        if (res.status === 401) throw new ApiError(401, 'The server did not accept the access token.');
        if (res.status === 429) throw new ApiError(429, 'Too many requests. Wait a moment.');
        throw new ApiError(res.status, detail || `The server answered with an error (${res.status}).`);
      }
      return (await res.json()) as T;
    } catch (e) {
      if (e instanceof ApiError) throw e;
      if (e instanceof Error && e.name === 'AbortError') {
        throw new ApiError(0, 'The server took too long to answer.');
      }
      throw new ApiError(0, 'Could not reach the server. Check the address and the Wi-Fi.');
    } finally {
      clearTimeout(timer);
    }
  }

  const post = <T>(path: string, body: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(body) });

  return {
    health: () => request<{ ok: boolean; mqtt: boolean }>('/api/health'),
    state: () => request<HomeSnapshot>('/api/state'),
    alerts: (limit = 50) => request<Alert[]>(`/api/alerts?limit=${limit}`),
    ackAlert: (id: number) => post<{ ok: boolean }>(`/api/alerts/${id}/ack`, undefined),
    access: (limit = 20) => request<AccessEntry[]>(`/api/access?limit=${limit}`),
    setActuator: (name: ActuatorName, action: 'on' | 'off' | 'toggle', seconds?: number) =>
      post(`/api/actuators/${name}`, seconds ? { action, seconds } : { action }),
    setDoor: (action: 'lock' | 'unlock') => post('/api/door', { action, source: 'app' }),
    setArmed: (armed: boolean) => post('/api/armed', { armed }),
    labResults: () => request<LabResult[]>('/api/lab-results'),
    addLabResult: (r: { result: LabResult['result']; target: string; notes: string; author: string }) =>
      post<{ id: number }>('/api/lab-results', r),
    readings: (metric: string, sinceSeconds = 3600) =>
      request<{ ts: number; value: number }[]>(`/api/readings/${metric}?since_seconds=${sinceSeconds}`),
  };
}

export type Api = ReturnType<typeof createApi>;
