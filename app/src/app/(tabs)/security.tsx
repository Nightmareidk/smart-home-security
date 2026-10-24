import { useCallback, useEffect, useState } from 'react';
import { Alert as NativeAlert, Text, View } from 'react-native';

import { Button, Card, Empty, Label, Muted, Pill, Screen, SwitchRow, Title } from '@/components/ui';
import { useConnection } from '@/lib/connection';
import { timeAgo } from '@/lib/format';
import type { AccessEntry } from '@/lib/types';
import { colors } from '@/theme';

export default function Security() {
  const { snapshot, api, act, status } = useConnection();
  const [access, setAccess] = useState<AccessEntry[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    if (!api) return;
    try {
      setAccess(await api.access(15));
    } catch {
      // the status pill already shows connection problems
    }
  }, [api]);

  useEffect(() => {
    load();
  }, [load, snapshot?.door.locked]);

  const locked = snapshot?.door.locked;

  const confirmUnlock = () =>
    NativeAlert.alert('Unlock the door?', 'Anyone at the door can walk in.', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Unlock', style: 'destructive', onPress: () => act((a) => a.setDoor('unlock')) },
    ]);

  return (
    <Screen
      refreshing={refreshing}
      onRefresh={async () => {
        setRefreshing(true);
        await load();
        setRefreshing(false);
      }}>
      <Title hint={status === 'live' ? undefined : 'Not connected to the house'}>Security</Title>

      <Card>
        <SwitchRow
          label="Armed"
          hint="Unknown people trigger an intruder alert"
          value={snapshot?.armed}
          onChange={(armed) => act((a) => a.setArmed(armed))}
        />
      </Card>

      <Card>
        <Label>Front door</Label>
        <Pill
          text={locked == null ? 'Unknown' : locked ? 'Locked' : 'Unlocked'}
          color={locked === false ? colors.warning : locked ? colors.accent : colors.muted}
        />
        <View style={{ flexDirection: 'row', gap: 8 }}>
          <View style={{ flex: 1 }}>
            <Button label="Lock" disabled={locked === true} onPress={() => act((a) => a.setDoor('lock'))} />
          </View>
          <View style={{ flex: 1 }}>
            <Button label="Unlock" tone="quiet" disabled={locked === false} onPress={confirmUnlock} />
          </View>
        </View>
      </Card>

      <Card>
        <Label>Who is home</Label>
        {snapshot?.people.length ? (
          snapshot.people.map((p) => (
            <View key={p.name} style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Text style={{ color: colors.text, fontSize: 16, textTransform: 'capitalize' }}>{p.name}</Text>
              <Muted>{p.present ? `Home · ${timeAgo(p.last_seen)}` : `Away · seen ${timeAgo(p.last_seen)}`}</Muted>
            </View>
          ))
        ) : (
          <Muted>Nobody recognised yet.</Muted>
        )}
      </Card>

      {snapshot?.last_camera ? (
        <Card>
          <Label>Last camera event</Label>
          <Text style={{ color: colors.text, fontSize: 16 }}>
            {snapshot.last_camera.type}
            {snapshot.last_camera.name ? ` · ${snapshot.last_camera.name}` : ' · stranger'}
          </Text>
          <Muted>{timeAgo(snapshot.last_camera.ts)}</Muted>
        </Card>
      ) : null}

      <Card>
        <Label>Door activity</Label>
        {access.length === 0 ? (
          <Empty text="No door activity yet." />
        ) : (
          access.map((e, i) => (
            <View key={`${e.ts}-${i}`} style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Text style={{ color: e.success ? colors.text : colors.danger, fontSize: 15 }}>
                {e.success ? 'Opened' : 'Refused'} · {e.method}
                {e.user ? ` · ${e.user}` : ''}
              </Text>
              <Muted>{timeAgo(e.ts)}</Muted>
            </View>
          ))
        )}
      </Card>
    </Screen>
  );
}
