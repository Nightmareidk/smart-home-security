import { useRouter } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { Button, Card, Empty, Label, Muted, Screen, Title } from '@/components/ui';
import { useConnection } from '@/lib/connection';
import { timeAgo } from '@/lib/format';
import type { LabResult } from '@/lib/types';
import { colors, radius } from '@/theme';

const OPTIONS: { value: LabResult['result']; label: string }[] = [
  { value: 'detected', label: 'Detected' },
  { value: 'not_detected', label: 'Not detected' },
  { value: 'inconclusive', label: 'Unclear' },
];

export default function Lab() {
  const { api, act } = useConnection();
  const router = useRouter();
  const [history, setHistory] = useState<LabResult[]>([]);
  const [result, setResult] = useState<LabResult['result']>('not_detected');
  const [target, setTarget] = useState('');
  const [notes, setNotes] = useState('');
  const [author, setAuthor] = useState('');

  const load = useCallback(async () => {
    if (!api) return;
    try {
      setHistory(await api.labResults());
    } catch {
      // keep what we have
    }
  }, [api]);

  useEffect(() => {
    load();
  }, [load]);

  const submit = async () => {
    const ok = await act((a) => a.addLabResult({ result, target: target.trim(), notes: notes.trim(), author: author.trim() }));
    if (ok) {
      setTarget('');
      setNotes('');
      load();
    }
  };

  return (
    <Screen>
      <Title hint="Mold test from the molecular biology experiment">Lab result</Title>
      <Card>
        <Label>Result</Label>
        <View style={{ flexDirection: 'row', gap: 8 }}>
          {OPTIONS.map((o) => (
            <Pressable
              key={o.value}
              accessibilityRole="radio"
              accessibilityState={{ selected: result === o.value }}
              onPress={() => setResult(o.value)}
              style={[styles.choice, result === o.value && styles.choiceOn]}>
              <Text style={{ color: result === o.value ? colors.accentText : colors.text, fontWeight: '600' }}>{o.label}</Text>
            </Pressable>
          ))}
        </View>
        <Label>What was tested</Label>
        <TextInput style={styles.input} value={target} onChangeText={setTarget} placeholder="For example: Aspergillus ITS region" placeholderTextColor={colors.muted} maxLength={80} />
        <Label>Notes</Label>
        <TextInput style={[styles.input, { minHeight: 80 }]} value={notes} onChangeText={setNotes} multiline placeholder="Band size, controls, anything useful" placeholderTextColor={colors.muted} maxLength={1000} />
        <Label>Entered by</Label>
        <TextInput style={styles.input} value={author} onChangeText={setAuthor} placeholder="Name" placeholderTextColor={colors.muted} maxLength={80} />
        <Button label="Save result" disabled={target.trim().length === 0} onPress={submit} />
      </Card>

      <Card>
        <Label>Earlier results</Label>
        {history.length === 0 ? (
          <Empty text="Nothing entered yet." />
        ) : (
          history.map((h) => (
            <View key={h.id} style={{ gap: 2 }}>
              <Text style={{ color: colors.text, fontSize: 16 }}>
                {OPTIONS.find((o) => o.value === h.result)?.label} · {h.target}
              </Text>
              <Muted>
                {timeAgo(h.ts)}
                {h.author ? ` · ${h.author}` : ''}
                {h.notes ? ` · ${h.notes}` : ''}
              </Muted>
            </View>
          ))
        )}
      </Card>
      <Button label="Close" tone="quiet" onPress={() => router.back()} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  choice: { flex: 1, alignItems: 'center', paddingVertical: 12, borderRadius: radius.md, backgroundColor: colors.cardAlt, borderWidth: 1, borderColor: colors.border },
  choiceOn: { backgroundColor: colors.accent, borderColor: colors.accent },
  input: { backgroundColor: colors.cardAlt, color: colors.text, borderRadius: radius.md, paddingHorizontal: 14, paddingVertical: 12, fontSize: 16, borderWidth: 1, borderColor: colors.border },
});
