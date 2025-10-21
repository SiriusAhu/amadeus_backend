# backend/schemas/command.py
from typing import Literal, Optional

from pydantic import BaseModel, Field


class RobotCommand(BaseModel):
    type: Literal["move", "beep", "stop"] = "move"
    direction: Optional[Literal["forward", "backward", "left", "right"]] = None
    speed: float = Field(default=0.0, ge=0)  # 默认 0
    duration: float = Field(default=0.0, ge=0)  # 默认 0
    distance: Optional[float] = None
    status: Optional[Literal["on", "off"]] = None

    def fill_defaults(self):
        """
        自动补全缺失字段 & 动作安全修正：
        - 若方向为空 => 转为 stop
        - 若速度和时长均为 0 => 转为 stop
        """
        if self.type == "move":
            if not self.direction or (self.speed == 0 and self.duration == 0):
                print("[安全保护] 检测到空方向或零运动量，自动转为 stop。")
                self.type = "stop"
                self.direction = None
                self.speed = 0.0
                self.duration = 0.0

        elif self.type == "beep":
            self.status = self.status or "on"

        elif self.type == "stop":
            self.direction = None
            self.speed = 0.0
            self.duration = 0.0

        return self


class AIResponse(BaseModel):
    text: str
    command: Optional[RobotCommand] = None
