import { Pill } from '@/components/ui';
import type { Status } from '@/lib/connection';
import { colors } from '@/theme';

const LABEL: Record<Status, [string, string]> = {
  unconfigured: ['Not set up', colors.warning],
  connecting: ['Connecting', colors.warning],
  live: ['Live', colors.accent],
  offline: ['Offline, retrying', colors.danger],
  unauthorised: ['Wrong token', colors.danger],
};

export function StatusPill({ status }: { status: Status }) {
  const [text, color] = LABEL[status];
  return <Pill text={text} color={color} />;
}
