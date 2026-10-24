import asyncio
import logging
import secrets
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .db import Database
from .hub import CommandFailed, CommandRefused, Hub
from .models import ActuatorCommand, ActuatorName, ArmedCommand, DoorCommand, LabResult
from .mqtt import MqttBridge
from .version import __version__

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("home")

settings = Settings()
if settings.api_token == "change-me":
    log.warning("HOME_API_TOKEN is the default. Fine for development, never for a real setup.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database(settings.db_path)
    bridge = MqttBridge(settings) if settings.mqtt_enabled else None
    hub = Hub(settings, db, bridge.publish if bridge else (lambda *a, **k: False))
    loop = asyncio.get_running_loop()
    if bridge:
        bridge.on_message = lambda topic, payload: asyncio.run_coroutine_threadsafe(hub.handle_message(topic, payload), loop)
        bridge.on_connected = hub.publish_armed
        bridge.start()
    ticker = asyncio.create_task(hub.run_ticker())
    app.state.hub, app.state.bridge = hub, bridge
    try:
        yield
    finally:
        ticker.cancel()
        if bridge:
            bridge.stop()


app = FastAPI(title="Smart Home Security", version=__version__, lifespan=lifespan, docs_url="/docs" if settings.env == "dev" else None, redoc_url=None, openapi_url="/openapi.json" if settings.env == "dev" else None)

if settings.cors_origins:
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])


# ---- protection: token check and a simple per-client rate limit ---------------

_hits: dict[str, deque] = defaultdict(deque)


def _token_ok(candidate: str | None) -> bool:
    return bool(candidate) and secrets.compare_digest(candidate.encode(), settings.api_token.encode())


async def require_auth(request: Request, authorization: Annotated[str | None, Header()] = None) -> None:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not _token_ok(token):
        raise HTTPException(status_code=401, detail="Not authorised")
    now = time.monotonic()
    hits = _hits[request.client.host if request.client else "unknown"]
    while hits and now - hits[0] > 60:
        hits.popleft()
    if len(hits) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Too many requests")
    hits.append(now)


Auth = Depends(require_auth)


def get_hub(request: Request) -> Hub:
    return request.app.state.hub


HubDep = Annotated[Hub, Depends(get_hub)]


# ---- routes ------------------------------------------------------------------


@app.get("/api/health")
async def health(hub: HubDep):
    bridge = app.state.bridge
    return {"ok": True, "mqtt": bool(bridge and bridge.connected), "version": __version__}


@app.get("/api/state", dependencies=[Auth])
async def state(hub: HubDep):
    return hub.snapshot()


@app.get("/api/alerts", dependencies=[Auth])
async def alerts(hub: HubDep, limit: Annotated[int, Query(ge=1, le=200)] = 50, open: bool = False):
    return hub.db.alerts(limit, only_open=open)


@app.post("/api/alerts/{alert_id}/ack", dependencies=[Auth])
async def ack_alert(alert_id: int, hub: HubDep):
    if not hub.db.ack_alert(alert_id):
        raise HTTPException(status_code=404, detail="No such alert")
    return {"ok": True}


@app.get("/api/readings/{metric}", dependencies=[Auth])
async def readings(
    metric: str,
    hub: HubDep,
    limit: Annotated[int, Query(ge=1, le=2000)] = 200,
    since_seconds: Annotated[float, Query(ge=0, le=30 * 86400)] = 3600,
):
    rows = hub.readings(metric, limit, since_seconds)
    if rows is None:
        raise HTTPException(status_code=400, detail="Bad metric name")
    return rows


@app.get("/api/access", dependencies=[Auth])
async def access(hub: HubDep, limit: Annotated[int, Query(ge=1, le=200)] = 50):
    return hub.db.access_log(limit)


@app.post("/api/actuators/{name}", dependencies=[Auth])
async def actuator(name: ActuatorName, cmd: ActuatorCommand, hub: HubDep):
    try:
        return hub.set_actuator(name, cmd)
    except CommandRefused as e:
        raise HTTPException(status_code=403, detail=str(e))
    except CommandFailed as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/door", dependencies=[Auth])
async def door(cmd: DoorCommand, hub: HubDep):
    try:
        return hub.set_door(cmd)
    except CommandRefused as e:
        raise HTTPException(status_code=403, detail=str(e))
    except CommandFailed as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/armed", dependencies=[Auth])
async def armed(cmd: ArmedCommand, hub: HubDep):
    await hub.set_armed(cmd.armed)
    return {"armed": cmd.armed}


@app.get("/api/lab-results", dependencies=[Auth])
async def lab_results(hub: HubDep, limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return hub.db.lab_results(limit)


@app.post("/api/lab-results", dependencies=[Auth], status_code=201)
async def add_lab_result(result: LabResult, hub: HubDep):
    return {"id": hub.add_lab_result(result)}


@app.websocket("/ws")
async def live(ws: WebSocket, token: str | None = None):
    if not _token_ok(token):
        await ws.close(code=1008)
        return
    hub: Hub = ws.app.state.hub
    await ws.accept()
    hub.clients.add(ws)
    try:
        await ws.send_json({"type": "state", "data": hub.snapshot()})
        while True:
            await ws.receive_text()  # the app does not send anything; this just notices a disconnect
    except WebSocketDisconnect:
        pass
    finally:
        hub.clients.discard(ws)
