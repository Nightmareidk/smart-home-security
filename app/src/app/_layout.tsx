import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';

import { ConnectionProvider, useConnection } from '@/lib/connection';
import { colors } from '@/theme';

function Gate() {
  const { loaded, config } = useConnection();
  const segments = useSegments();
  const router = useRouter();

  // First launch: send the user to set the server address.
  useEffect(() => {
    if (loaded && !config && segments[0] !== 'settings') router.replace('/settings');
  }, [loaded, config, segments, router]);

  return (
    <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.bg } }}>
      <Stack.Screen name="(tabs)" />
      <Stack.Screen name="settings" options={{ presentation: 'modal' }} />
      <Stack.Screen name="lab" options={{ presentation: 'modal' }} />
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <ConnectionProvider>
      <StatusBar style="light" />
      <Gate />
    </ConnectionProvider>
  );
}
