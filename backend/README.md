# Backend

The server on the laptop (Python, FastAPI). It:

- receives messages from the boards and the AI programs over MQTT (`docs/CONTRACT.md`),
- keeps the current state of the house and saves readings, alerts and door activity in SQLite,
- applies the alert rules (mold risk, fire, intruder, thirsty plant, failed unlocks, board offline),
- sends live updates to the app over a WebSocket,
- takes commands from the app (switches, door, armed) and sends them to the boards.

## Layout

| File | What it does |
|---|---|
| `app/main.py` | The web routes, token check and rate limit |
| `app/hub.py` | The middle: takes in messages, runs commands, raises alerts |
| `app/rules.py` | The alert rules (pure logic, easy to test) |
| `app/state.py` | The current picture of the house, with checks on every incoming value |
| `app/db.py` | SQLite storage |
| `app/mqtt.py` | The broker connection (reconnects by itself) |
| `app/config.py` | Settings, read from environment variables starting with `HOME_` |
| `tools/dev_broker.py` | A tiny broker for development |
| `tests/` | 30 tests: `python -m pytest` |

## Safety rules built in

- Every route except `/api/health` needs the access token.
- The door can never be unlocked with `source: "voice"`.
- The pump always gets a time limit (10 s by default, 60 s at most).
- Messages with impossible values, bad JSON or too large a size are ignored.
- API docs are switched off unless `HOME_ENV=dev`. Outside dev, the server will not start with the default token.

See `docs/RUNNING.md` to start it.
