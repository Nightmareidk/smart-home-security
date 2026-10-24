# Running the software (no hardware needed)

You need Python 3.11+ and Node 20+. Open four terminals in the repo folder.

## 1. Message broker (the post office between boards, server and app)

For development, a small broker written in Python is enough:

```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt     # Windows
.venv\Scripts\python tools/dev_broker.py
```

For the real boards on your Wi-Fi, use Mosquitto instead (needs Docker):

```bash
docker compose up -d
```

## 2. Server

```bash
cd backend
copy .env.example .env          # then set HOME_API_TOKEN to something of your own
.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Check it: open http://localhost:8000/api/health. In development there is also an
interactive page at http://localhost:8000/docs.

Tests: `.venv\Scripts\python -m pytest` (inside `backend`).

## 3. Pretend house

```bash
cd simulator
..\backend\.venv\Scripts\python sim.py
```

In another terminal, make things happen:

```bash
..\backend\.venv\Scripts\python sim.py scenario list
..\backend\.venv\Scripts\python sim.py scenario mold
```

Add `--speed 5` to the first command to make everything happen five times faster.
For a quick mold-risk demo set `HOME_MOLD_HOLD_SECONDS=10` in `backend/.env`.

## 4. App

```bash
cd app
npm install
npx expo start
```

- **On a phone:** install Expo Go, scan the QR code. In the app's Settings enter the laptop's
  Wi-Fi address, for example `http://192.168.1.20:8000`, and the token from `.env`.
  The phone and laptop must be on the same Wi-Fi, and Windows Firewall must allow port 8000.
- **In a browser (quick look):** press `w`. Add `HOME_CORS_ORIGINS=["http://localhost:8081"]`
  to `backend/.env` so the browser is allowed to talk to the server.

## What to try

| Do this | You should see |
|---|---|
| `sim.py scenario mold`, wait for the hold time | A mold-risk banner and an alert |
| Flip the Fan switch in the app | The simulator prints `fan -> ON` and the switch stays on |
| Arm the system, then `scenario intruder` | An intruder alert |
| `scenario known` | Sara shows as home and the door opens for 5 seconds |
| `scenario failed` | A door-attempts alert |
| `scenario fire` | A critical fire alert |
