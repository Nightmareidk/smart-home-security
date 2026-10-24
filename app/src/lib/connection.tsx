import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Alert as NativeAlert } from 'react-native';

import { ApiError, cleanBaseUrl, createApi, type Api } from './api';
import { getItem, setItem } from './storage';
import type { Alert, HomeSnapshot, LiveMessage } from './types';

export type Status = 'unconfigured' | 'connecting' | 'live' | 'offline' | 'unauthorised';

export interface Config {
  url: string;
  token: string;
}

interface Connection {
  loaded: boolean;
  config: Config | null;
  status: Status;
  snapshot: HomeSnapshot | null;
  alerts: Alert[];
  api: Api | null;
  saveConfig: (config: Config) => Promise<void>;
  refreshAlerts: () => Promise<void>;
  /** Run something the user asked for; shows a message if it fails. */
  act: (fn: (api: Api) => Promise<unknown>) => Promise<boolean>;
}

const Ctx = createContext<Connection | null>(null);

const URL_KEY = 'home.server_url';
const TOKEN_KEY = 'home.api_token';
const MAX_BACKOFF_MS = 15000;

function toWsUrl(base: string, token: string): string {
  return `${cleanBaseUrl(base).replace(/^http/, 'ws')}/ws?token=${encodeURIComponent(token)}`;
}

export function ConnectionProvider({ children }: { children: ReactNode }) {
  const [loaded, setLoaded] = useState(false);
  const [config, setConfig] = useState<Config | null>(null);
  const [status, setStatus] = useState<Status>('unconfigured');
  const [snapshot, setSnapshot] = useState<HomeSnapshot | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const api = useMemo(() => (config ? createApi(config.url, config.token) : null), [config]);

  useEffect(() => {
    (async () => {
      const [url, token] = await Promise.all([getItem(URL_KEY), getItem(TOKEN_KEY)]);
      if (url && token) setConfig({ url, token });
      setLoaded(true);
    })();
  }, []);

  const saveConfig = useCallback(async (next: Config) => {
    const clean = { url: cleanBaseUrl(next.url), token: next.token.trim() };
    await setItem(URL_KEY, clean.url);
    await setItem(TOKEN_KEY, clean.token);
    setSnapshot(null);
    setConfig(clean);
  }, []);

  const refreshAlerts = useCallback(async () => {
    if (!api) return;
    try {
      setAlerts(await api.alerts());
    } catch {
      // the live connection shows the problem; keep the old list
    }
  }, [api]);

  // Live connection: reconnects by itself, waiting a little longer each time it fails.
  useEffect(() => {
    if (!config) {
      setStatus('unconfigured');
      return;
    }
    let closed = false;
    let socket: WebSocket | null = null;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;

    const connect = () => {
      setStatus('connecting');
      socket = new WebSocket(toWsUrl(config.url, config.token));
      socket.onopen = () => {
        attempt = 0;
        setStatus('live');
        refreshAlerts();
      };
      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(String(event.data)) as LiveMessage;
          if (message.type === 'state') setSnapshot(message.data);
          else if (message.type === 'alert') setAlerts((old) => [message.data, ...old.filter((a) => a.id !== message.data.id)].slice(0, 100));
        } catch {
          // ignore anything that is not a message we know
        }
      };
      socket.onclose = (event) => {
        if (closed) return;
        if (event.code === 1008) {
          setStatus('unauthorised');
          return;
        }
        setStatus('offline');
        attempt += 1;
        timer = setTimeout(connect, Math.min(1000 * 2 ** attempt, MAX_BACKOFF_MS));
      };
      socket.onerror = () => {
        // onclose follows and handles the retry
      };
    };

    connect();
    return () => {
      closed = true;
      if (timer) clearTimeout(timer);
      socket?.close();
    };
  }, [config, refreshAlerts]);

  const act = useCallback(
    async (fn: (api: Api) => Promise<unknown>) => {
      if (!api) return false;
      try {
        await fn(api);
        return true;
      } catch (e) {
        const message = e instanceof ApiError ? e.message : 'Something went wrong.';
        NativeAlert.alert('Could not do that', message);
        return false;
      }
    },
    [api],
  );

  const value = useMemo(
    () => ({ loaded, config, status, snapshot, alerts, api, saveConfig, refreshAlerts, act }),
    [loaded, config, status, snapshot, alerts, api, saveConfig, refreshAlerts, act],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useConnection(): Connection {
  const value = useContext(Ctx);
  if (!value) throw new Error('useConnection must be used inside ConnectionProvider');
  return value;
}
