import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { StyleSheet, Text, TextInput } from 'react-native';

import { Button, Card, Label, Muted, Screen, Title } from '@/components/ui';
import { ApiError, createApi } from '@/lib/api';
import { useConnection } from '@/lib/connection';
import { versionLabel } from '@/version';
import { colors, radius } from '@/theme';

export default function Settings() {
  const { config, saveConfig } = useConnection();
  const router = useRouter();
  const [url, setUrl] = useState(config?.url ?? 'http://');
  const [token, setToken] = useState(config?.token ?? '');
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  // The saved values load a moment after the first draw, so copy them in when they arrive.
  useEffect(() => {
    if (config) {
      setUrl(config.url);
      setToken(config.token);
    }
  }, [config]);

  const valid = /^https?:\/\/.+/i.test(url.trim()) && token.trim().length > 0;

  const test = async () => {
    setBusy(true);
    setResult(null);
    try {
      const api = createApi(url, token.trim());
      const health = await api.health();
      await api.state(); // checks the token too
      setResult({ ok: true, text: health.mqtt ? 'Connected. The house is reachable.' : 'Server reached, but it is not connected to the house yet (broker).' });
    } catch (e) {
      setResult({ ok: false, text: e instanceof ApiError ? e.message : 'Something went wrong.' });
    } finally {
      setBusy(false);
    }
  };

  const save = async () => {
    await saveConfig({ url, token });
    router.replace('/');
  };

  return (
    <Screen>
      <Title hint="Where the house server runs">Settings</Title>
      <Card>
        <Label>Server address</Label>
        <TextInput
          style={styles.input}
          value={url}
          onChangeText={setUrl}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
          placeholder="http://192.168.1.20:8000"
          placeholderTextColor={colors.muted}
          accessibilityLabel="Server address"
        />
        <Muted>Use the laptop's Wi-Fi address (not localhost). The phone and laptop must be on the same Wi-Fi.</Muted>

        <Label>Access token</Label>
        <TextInput
          style={styles.input}
          value={token}
          onChangeText={setToken}
          autoCapitalize="none"
          autoCorrect={false}
          secureTextEntry
          placeholder="HOME_API_TOKEN from the server"
          placeholderTextColor={colors.muted}
          accessibilityLabel="Access token"
        />
      </Card>

      {result ? <Text style={{ color: result.ok ? colors.accent : colors.danger, fontSize: 15 }}>{result.text}</Text> : null}

      <Button label={busy ? 'Testing…' : 'Test connection'} tone="quiet" disabled={!valid || busy} onPress={test} />
      <Button label="Save" disabled={!valid || busy} onPress={save} />
      {config ? <Button label="Close" tone="quiet" onPress={() => router.back()} /> : null}
      <Muted>Smart Home · {versionLabel()}</Muted>
    </Screen>
  );
}

const styles = StyleSheet.create({
  input: {
    backgroundColor: colors.cardAlt,
    color: colors.text,
    borderRadius: radius.md,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
});
