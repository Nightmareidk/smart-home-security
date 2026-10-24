import type { ReactNode } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Switch, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { colors, radius, space } from '@/theme';

export function Screen({
  children,
  onRefresh,
  refreshing = false,
}: {
  children: ReactNode;
  onRefresh?: () => void;
  refreshing?: boolean;
}) {
  const insets = useSafeAreaInsets();
  return (
    <ScrollView
      style={{ backgroundColor: colors.bg }}
      contentContainerStyle={{ padding: space.lg, paddingTop: insets.top + space.lg, gap: space.md }}
      refreshControl={onRefresh ? <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.accent} /> : undefined}>
      {children}
    </ScrollView>
  );
}

export function Title({ children, hint }: { children: ReactNode; hint?: string }) {
  return (
    <View style={{ gap: 2 }}>
      <Text style={styles.title} accessibilityRole="header">
        {children}
      </Text>
      {hint ? <Text style={styles.muted}>{hint}</Text> : null}
    </View>
  );
}

export function Card({ children, style }: { children: ReactNode; style?: StyleProp<ViewStyle> }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function Label({ children }: { children: ReactNode }) {
  return <Text style={styles.label}>{children}</Text>;
}

export function Muted({ children }: { children: ReactNode }) {
  return <Text style={styles.muted}>{children}</Text>;
}

export function Big({ children, unit }: { children: ReactNode; unit?: string }) {
  return (
    <Text style={styles.big}>
      {children}
      {unit ? <Text style={styles.bigUnit}> {unit}</Text> : null}
    </Text>
  );
}

export function Pill({ text, color }: { text: string; color: string }) {
  return (
    <View style={[styles.pill, { borderColor: color }]}>
      <View style={[styles.dot, { backgroundColor: color }]} />
      <Text style={[styles.pillText, { color }]}>{text}</Text>
    </View>
  );
}

export function Button({
  label,
  onPress,
  tone = 'primary',
  disabled,
}: {
  label: string;
  onPress: () => void;
  tone?: 'primary' | 'quiet' | 'danger';
  disabled?: boolean;
}) {
  const background = tone === 'primary' ? colors.accent : tone === 'danger' ? colors.danger : colors.cardAlt;
  const color = tone === 'quiet' ? colors.text : colors.accentText;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [styles.button, { backgroundColor: background, opacity: disabled ? 0.4 : pressed ? 0.8 : 1 }]}>
      <Text style={[styles.buttonText, { color }]}>{label}</Text>
    </Pressable>
  );
}

export function SwitchRow({
  label,
  hint,
  value,
  onChange,
  disabled,
}: {
  label: string;
  hint?: string;
  value: boolean | null | undefined;
  onChange: (next: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <View style={styles.switchRow}>
      <View style={{ flex: 1 }}>
        <Text style={styles.rowLabel}>{label}</Text>
        {hint ? <Text style={styles.muted}>{hint}</Text> : null}
      </View>
      <Switch
        accessibilityLabel={label}
        value={!!value}
        disabled={disabled || value == null}
        onValueChange={onChange}
        trackColor={{ true: colors.accent, false: colors.border }}
      />
    </View>
  );
}

export function Meter({ value, max = 100, color = colors.accent }: { value: number; max?: number; color?: string }) {
  const pct = Math.max(0, Math.min(1, value / max));
  return (
    <View style={styles.meterTrack}>
      <View style={[styles.meterFill, { width: `${pct * 100}%`, backgroundColor: color }]} />
    </View>
  );
}

export function Empty({ text }: { text: string }) {
  return (
    <View style={{ paddingVertical: space.xl, alignItems: 'center' }}>
      <Text style={styles.muted}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  title: { color: colors.text, fontSize: 28, fontWeight: '700', letterSpacing: -0.5 },
  card: { backgroundColor: colors.card, borderRadius: radius.lg, padding: space.lg, gap: space.sm, borderWidth: 1, borderColor: colors.border },
  label: { color: colors.muted, fontSize: 12, fontWeight: '600', letterSpacing: 0.8, textTransform: 'uppercase' },
  muted: { color: colors.muted, fontSize: 14 },
  big: { color: colors.text, fontSize: 36, fontWeight: '700', letterSpacing: -1 },
  bigUnit: { color: colors.muted, fontSize: 16, fontWeight: '500' },
  pill: { flexDirection: 'row', alignItems: 'center', gap: 6, borderWidth: 1, borderRadius: radius.pill, paddingHorizontal: 10, paddingVertical: 4, alignSelf: 'flex-start' },
  dot: { width: 7, height: 7, borderRadius: 4 },
  pillText: { fontSize: 13, fontWeight: '600' },
  button: { borderRadius: radius.md, paddingVertical: 14, paddingHorizontal: space.lg, alignItems: 'center', minHeight: 48, justifyContent: 'center' },
  buttonText: { fontSize: 16, fontWeight: '700' },
  switchRow: { flexDirection: 'row', alignItems: 'center', gap: space.md, minHeight: 48 },
  rowLabel: { color: colors.text, fontSize: 16, fontWeight: '500' },
  meterTrack: { height: 8, borderRadius: 4, backgroundColor: colors.cardAlt, overflow: 'hidden' },
  meterFill: { height: 8, borderRadius: 4 },
});
