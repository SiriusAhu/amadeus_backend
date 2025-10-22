"""机器人指令和 AI 响应的数据模型定义."""

from typing import Literal

from loguru import logger as lg
from pydantic import BaseModel, Field


class RobotCommand(BaseModel):
    """机器人指令模型."""

    type: Literal["move", "beep", "stop"] = "move"
    direction: Literal["forward", "backward", "left", "right"] | None = None
    speed: float = Field(default=0.0, ge=0, description="运动速度 (m/s)")
    duration: float = Field(default=0.0, ge=0, description="运动持续时间 (s)")
    distance: float | None = Field(default=None, description="运动距离 (m)")
    status: Literal["on", "off"] | None = Field(default=None, description="蜂鸣器状态")

    def fill_defaults(self) -> "RobotCommand":
        """自动补全缺失字段并进行安全修正.

        安全规则:
        - 若方向为空 => 转为 stop
        - 若速度和时长均为 0 => 转为 stop

        Returns:
            修正后的指令对象
        """
        if self.type == "move":
            if not self.direction or (self.speed == 0 and self.duration == 0):
                lg.warning("[安全保护] 检测到空方向或零运动量，自动转为 stop")
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
    """AI 响应模型，包含文本和可选的机器人指令."""

    text: str = Field(description="AI 生成的响应文本")
    command: RobotCommand | None = Field(default=None, description="可选的机器人指令")
