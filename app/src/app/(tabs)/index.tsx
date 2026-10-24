import { useRouter } from 'expo-router';
import { Text, View } from 'react-native';

import { StatusPill } from '@/components/status-pill';
import { Big, Button, Card, Label, Muted, Pill, Screen, SwitchRow, Title } from '@/components/ui';
import { ALERT_TITLE, num, timeAgo } from '@/lib/format';
import { useConnection } from '@/lib/connection';
import { colors, severityColor } from '@/theme';

export default function Home() {
  const { status, snapshot, alerts, act } = useConnection();
  const router = useRouter();
  const env = snapshot?.env;
  const latest = alerts.find((a) => !a.acknowledged);

  return (
    <Screen>
      <View style={{ gap: 8 }}>
        <Title>Home</Title>
        <StatusPill status={status} />
      </View>

      {status === 'unconfigured' ? (
        <Card>
          <Muted>Set the server address to connect to the house.</Muted>
          <Button label="Open settings" onPress={() => router.push('/settings')} />
        </Card>
      ) : null}

      {snapshot?.mold.risk ? (
        <Card style={{ borderColor: colors.warning }}>
          <Label>Mold risk</Label>
          <Text style={{ color: colors.text, fontSize: 16 }}>
            The air has been damp and warm for a while. Switch on the fan or open a window.
          </Text>
          <Button label="Turn on the fan" tone="quiet" onPress={() => act((api) => api.setActuator('fan', 'on'))} />
        </Card>
      ) : null}

      <Card>
        <Label>Bathroom climate</Label>
        {env && env.temp_c !== undefined ? (
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <Big unit="°C">{num(env.temp_c, 1)}</Big>
            <Big unit="%">{num(env.humidity)}</Big>
          </View>
        ) : (
          <Muted>{status === 'live' ? 'Waiting for the first reading…' : 'No data yet.'}</Muted>
        )}
        {env?.iaq !== undefined ? <Muted>Air quality {num(env.iaq)} / 100 (higher is better)</Muted> : null}
      </Card>

      <Card>
        <Label>Security</Label>
        <View style={{ flexDirection: 'row', gap: 8, flexWrap: 'wrap' }}>
          <Pill text={snapshot?.armed ? 'Armed' : 'Disarmed'} color={snapshot?.armed ? colors.accent : colors.muted} />
          <Pill
            text={snapshot?.door.locked == null ? 'Door unknown' : snapshot.door.locked ? 'Door locked' : 'Door unlocked'}
            color={snapshot?.door.locked === false ? colors.warning : colors.accent}
          />
        </View>
      </Card>

      <Card>
        <Label>Quick controls</Label>
        <SwitchRow label="Light" value={snapshot?.actuators.light} onChange={(on) => act((api) => api.setActuator('light', on ? 'on' : 'off'))} />
        <SwitchRow label="Fan" value={snapshot?.actuators.fan} onChange={(on) => act((api) => api.setActuator('fan', on ? 'on' : 'off'))} />
        <SwitchRow label="Humidifier" value={snapshot?.actuators.humidifier} onChange={(on) => act((api) => api.setActuator('humidifier', on ? 'on' : 'off'))} />
      </Card>

      {latest ? (
        <Card style={{ borderColor: severityColor[latest.severity] }}>
          <Label>{ALERT_TITLE[latest.type] ?? latest.type}</Label>
          <Text style={{ color: colors.text, fontSize: 16 }}>{latest.message}</Text>
          <Muted>{timeAgo(latest.ts)}</Muted>
        </Card>
      ) : null}

      <Button label="Lab results" tone="quiet" onPress={() => router.push('/lab')} />
      <Button label="Settings" tone="quiet" onPress={() => router.push('/settings')} />
    </Screen>
  );
}
