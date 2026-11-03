import { useRef, useState, type ComponentRef } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { StatusPill } from '@/components/status-pill';
import { Muted } from '@/components/ui';
import { ApiError } from '@/lib/api';
import { useConnection } from '@/lib/connection';
import { colors, radius, space } from '@/theme';

interface Message {
  from: 'me' | 'jarvis';
  text: string;
  failed?: boolean;
}

const EXAMPLES = ['Turn on the light', 'Is there a mold risk?', 'Who is home?', 'Water the plants', 'Lock the door', 'Is everything okay?'];

export default function Jarvis() {
  const { api, status } = useConnection();
  const insets = useSafeAreaInsets();
  const [messages, setMessages] = useState<Message[]>([
    { from: 'jarvis', text: "Hi, I'm Jarvis. Type a command or a question. Say help to hear what I can do. I never unlock the door." },
  ]);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const scroll = useRef<ComponentRef<typeof ScrollView>>(null);

  const add = (m: Message) => {
    setMessages((old) => [...old, m]);
    setTimeout(() => scroll.current?.scrollToEnd({ animated: true }), 50);
  };

  const send = async (raw: string) => {
    const t = raw.trim();
    if (!t || busy || !api) return;
    setText('');
    add({ from: 'me', text: t });
    setBusy(true);
    try {
      const res = await api.jarvis(t);
      add({ from: 'jarvis', text: res.reply, failed: !res.ok });
    } catch (e) {
      add({ from: 'jarvis', text: e instanceof ApiError ? e.message : 'Something went wrong.', failed: true });
    } finally {
      setBusy(false);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: colors.bg }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={{ paddingTop: insets.top + space.lg, paddingHorizontal: space.lg, gap: 8 }}>
        <Text style={styles.title} accessibilityRole="header">
          Jarvis
        </Text>
        <StatusPill status={status} />
      </View>
      <ScrollView ref={scroll} style={{ flex: 1 }} contentContainerStyle={{ padding: space.lg, gap: space.sm }} keyboardShouldPersistTaps="handled">
        {messages.map((m, i) => (
          <View key={i} style={[styles.bubble, m.from === 'me' ? styles.mine : styles.theirs, m.failed && styles.failed]}>
            <Text style={{ color: m.from === 'me' ? colors.accentText : colors.text, fontSize: 16 }}>{m.text}</Text>
          </View>
        ))}
        {busy ? <Muted>Jarvis is thinking…</Muted> : null}
      </ScrollView>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ flexGrow: 0 }} contentContainerStyle={{ paddingHorizontal: space.lg, gap: 8, paddingBottom: 8 }} keyboardShouldPersistTaps="handled">
        {EXAMPLES.map((e) => (
          <Pressable key={e} onPress={() => send(e)} accessibilityRole="button" accessibilityLabel={e} style={styles.chip}>
            <Text style={{ color: colors.text, fontSize: 13 }}>{e}</Text>
          </Pressable>
        ))}
      </ScrollView>
      <View style={[styles.inputRow, { paddingBottom: Math.max(insets.bottom, space.md) }]}>
        <TextInput
          style={styles.input}
          value={text}
          onChangeText={setText}
          onSubmitEditing={() => send(text)}
          placeholder="Ask Jarvis…"
          placeholderTextColor={colors.muted}
          returnKeyType="send"
          maxLength={200}
          accessibilityLabel="Message to Jarvis"
        />
        <Pressable
          onPress={() => send(text)}
          disabled={busy || !text.trim()}
          accessibilityRole="button"
          accessibilityLabel="Send"
          style={[styles.send, { opacity: busy || !text.trim() ? 0.4 : 1 }]}>
          <Text style={{ color: colors.accentText, fontWeight: '700' }}>Send</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  title: { color: colors.text, fontSize: 28, fontWeight: '700', letterSpacing: -0.5 },
  bubble: { maxWidth: '85%', borderRadius: radius.lg, paddingHorizontal: 14, paddingVertical: 10 },
  mine: { alignSelf: 'flex-end', backgroundColor: colors.accent },
  theirs: { alignSelf: 'flex-start', backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border },
  failed: { borderColor: colors.warning },
  chip: { borderRadius: radius.pill, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card, paddingHorizontal: 12, paddingVertical: 8 },
  inputRow: { flexDirection: 'row', gap: 8, paddingHorizontal: space.lg, paddingTop: 8, borderTopWidth: 1, borderTopColor: colors.border, backgroundColor: colors.card },
  input: { flex: 1, backgroundColor: colors.cardAlt, color: colors.text, borderRadius: radius.md, paddingHorizontal: 14, paddingVertical: 12, fontSize: 16, borderWidth: 1, borderColor: colors.border },
  send: { backgroundColor: colors.accent, borderRadius: radius.md, paddingHorizontal: 16, justifyContent: 'center' },
});
