import appJson from '../app.json';

// "1.0.0" in app.json is shown as "Beta 1.0". See "Versions" in CONTRIBUTING.md.
export function versionLabel(): string {
  const [major, minor] = appJson.expo.version.split('.');
  return `Beta ${major}.${minor ?? 0}`;
}
