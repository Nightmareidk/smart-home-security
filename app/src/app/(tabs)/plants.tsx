import { Text, View } from 'react-native';

import { Button, Card, Label, Meter, Muted, Screen, SwitchRow, Title } from '@/components/ui';
import { useConnection } from '@/lib/connection';
import { num } from '@/lib/format';
import { colors } from '@/theme';

const DRY_BELOW = 25;
const WATER_SECONDS = 10;

export default function Plants() {
  const { snapshot, act } = useConnection();
  const pumpOn = snapshot?.actuators.pump;

  return (
    <Screen>
      <Title>Plants</Title>

      <Card>
        <Label>Soil moisture</Label>
        {snapshot?.soil.length ? (
          snapshot.soil.map((p) => {
            const dry = p.moisture_pct < DRY_BELOW;
            return (
              <View key={p.id} style={{ gap: 6 }}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                  <Text style={{ color: colors.text, fontSize: 16 }}>Plant {p.id}</Text>
                  <Text style={{ color: dry ? colors.warning : colors.muted, fontSize: 15 }}>
                    {num(p.moisture_pct)}%{dry ? ' · dry' : ''}
                  </Text>
                </View>
                <Meter value={p.moisture_pct} color={dry ? colors.warning : colors.accent} />
              </View>
            );
          })
        ) : (
          <Muted>No plant readings yet.</Muted>
        )}
      </Card>

      <Card>
        <Label>Watering</Label>
        <Muted>The pump runs for {WATER_SECONDS} seconds, then stops by itself.</Muted>
        <Button
          label={pumpOn ? 'Watering…' : 'Water now'}
          disabled={!!pumpOn}
          onPress={() => act((api) => api.setActuator('pump', 'on', WATER_SECONDS))}
        />
      </Card>

      <Card>
        <Label>Light</Label>
        <SwitchRow
          label="Grow light"
          value={snapshot?.actuators.growlight}
          onChange={(on) => act((api) => api.setActuator('growlight', on ? 'on' : 'off'))}
        />
      </Card>
    </Screen>
  );
}
