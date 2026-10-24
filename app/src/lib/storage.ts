import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

// On the phone the access token goes in the secure store. The browser preview has no secure
// store, so it falls back to localStorage (only meant for development).

export async function getItem(key: string): Promise<string | null> {
  try {
    if (Platform.OS === 'web') return globalThis.localStorage?.getItem(key) ?? null;
    return await SecureStore.getItemAsync(key);
  } catch {
    return null;
  }
}

export async function setItem(key: string, value: string): Promise<void> {
  if (Platform.OS === 'web') {
    globalThis.localStorage?.setItem(key, value);
    return;
  }
  await SecureStore.setItemAsync(key, value);
}
