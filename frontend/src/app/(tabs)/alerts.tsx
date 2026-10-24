import { useState } from 'react';
import { Text, View } from 'react-native';

import { Button, Card, Empty, Label, Muted, Screen, Title } from '@/components/ui';
import { useConnection } from '@/lib/connection';
import { ALERT_TITLE, timeAgo } from '@/lib/format';
import { colors, severityColor } from '@/theme';

export default function Alerts() {
  const { alerts, act, refreshAlerts } = useConnection();
  const [refreshing, setRefreshing] = useState(false);

  const acknowledge = async (id: number) => {
    if (await act((api) => api.ackAlert(id))) await refreshAlerts();
  };

  return (
    <Screen
      refreshing={refreshing}
      onRefresh={async () => {
        setRefreshing(true);
        await refreshAlerts();
        setRefreshing(false);
      }}>
      <Title>Alerts</Title>
      {alerts.length === 0 ? (
        <Empty text="No alerts. All quiet." />
      ) : (
        alerts.map((a) => (
          <Card key={a.id} style={{ borderColor: a.acknowledged ? colors.border : severityColor[a.severity], opacity: a.acknowledged ? 0.6 : 1 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Label>{ALERT_TITLE[a.type] ?? a.type}</Label>
              <Muted>{timeAgo(a.ts)}</Muted>
            </View>
            <Text style={{ color: colors.text, fontSize: 16 }}>{a.message}</Text>
            {a.acknowledged ? null : <Button label="Got it" tone="quiet" onPress={() => acknowledge(a.id)} />}
          </Card>
        ))
      )}
    </Screen>
  );
}
