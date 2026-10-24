// Placeholder look. The real visual design is chosen later; everything reads from here,
// so changing the look means changing this file.

export const colors = {
  bg: '#0E1514',
  card: '#16201F',
  cardAlt: '#1D2928',
  border: '#263634',
  text: '#E8F0EE',
  muted: '#8DA09C',
  accent: '#3DDC97',
  accentText: '#06231A',
  warning: '#F5B94A',
  danger: '#FF6B5E',
  info: '#6CB6FF',
};

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24 };
export const radius = { sm: 8, md: 14, lg: 20, pill: 999 };

export const severityColor = {
  info: colors.info,
  warning: colors.warning,
  critical: colors.danger,
} as const;
