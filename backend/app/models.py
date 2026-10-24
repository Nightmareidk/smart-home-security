from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ACTUATORS = ("light", "growlight", "pump", "fan", "humidifier", "heater", "buzzer")
ActuatorName = Literal["light", "growlight", "pump", "fan", "humidifier", "heater", "buzzer"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ActuatorCommand(Strict):
    action: Literal["on", "off", "toggle"]
    seconds: float | None = Field(default=None, gt=0, le=600)


class DoorCommand(Strict):
    action: Literal["lock", "unlock"]
    # Who is asking. Voice may never unlock the door (see hub.py).
    source: Literal["app", "voice", "auto"] = "app"


class ArmedCommand(Strict):
    armed: bool


class LabResult(Strict):
    result: Literal["detected", "not_detected", "inconclusive"]
    target: str = Field(min_length=1, max_length=80)
    notes: str = Field(default="", max_length=1000)
    author: str = Field(default="", max_length=80)
