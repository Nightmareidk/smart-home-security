import { Text } from 'react-native';

import { Card, Label, Muted, Screen, Title } from '@/components/ui';
import { colors } from '@/theme';

const EXAMPLES = [
  'Jarvis, turn the light on',
  'Jarvis, is there a mold risk?',
  'Jarvis, who is home?',
  'Jarvis, water the plants',
  'Jarvis, lock the door',
];

export default function Jarvis() {
  return (
    <Screen>
      <Title hint="Voice assistant">Jarvis</Title>
      <Card>
        <Label>Coming soon</Label>
        <Muted>
          Jarvis listens through the house microphone and answers out loud. This tab will show what it heard and did, and let you type to it.
        </Muted>
      </Card>
      <Card>
        <Label>You will be able to say</Label>
        {EXAMPLES.map((e) => (
          <Text key={e} style={{ color: colors.text, fontSize: 16 }}>
            “{e}”
          </Text>
        ))}
      </Card>
      <Muted>The door can never be unlocked by voice. Use the app, fingerprint, keypad or face.</Muted>
    </Screen>
  );
}
