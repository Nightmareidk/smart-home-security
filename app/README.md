# App

The phone app that controls the house (React Native with Expo, TypeScript).

| Tab | What it does |
|---|---|
| Home | Bathroom climate, mold-risk banner, security state, quick switches, latest alert |
| Security | Arm and disarm, lock and unlock the door, who is home, door activity |
| Plants | Soil moisture, water now, grow light |
| Jarvis | Placeholder until the voice assistant is built |
| Alerts | Alert history, with "Got it" |

Also: a Settings screen (server address and token, kept in the phone's secure storage) and a
Lab result form for the molecular biology student.

The look is a plain placeholder. Everything reads its colours and spacing from `src/theme.ts`,
so the final design can replace it without touching the screens.

Layout: `src/app` has the screens, `src/lib` the server connection (`connection.tsx` keeps a
live WebSocket and reconnects by itself), `src/components` the shared pieces.

See `docs/RUNNING.md` to start it.
