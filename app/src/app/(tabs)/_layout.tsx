import { Ionicons } from '@expo/vector-icons';
import { Tabs } from 'expo-router';
import type { ColorValue } from 'react-native';

import { colors } from '@/theme';

type IconName = React.ComponentProps<typeof Ionicons>['name'];

function icon(name: IconName, focused: IconName) {
  return ({ color, focused: isFocused }: { color: ColorValue; focused: boolean }) => (
    <Ionicons name={isFocused ? focused : name} size={24} color={color as string} />
  );
}

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: { backgroundColor: colors.card, borderTopColor: colors.border },
      }}>
      <Tabs.Screen name="index" options={{ title: 'Home', tabBarIcon: icon('home-outline', 'home') }} />
      <Tabs.Screen name="security" options={{ title: 'Security', tabBarIcon: icon('shield-outline', 'shield') }} />
      <Tabs.Screen name="plants" options={{ title: 'Plants', tabBarIcon: icon('leaf-outline', 'leaf') }} />
      <Tabs.Screen name="jarvis" options={{ title: 'Jarvis', tabBarIcon: icon('mic-outline', 'mic') }} />
      <Tabs.Screen name="alerts" options={{ title: 'Alerts', tabBarIcon: icon('notifications-outline', 'notifications') }} />
    </Tabs>
  );
}
