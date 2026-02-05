from __future__ import annotations

from datetime import datetime
from typing import Any, List

from pydantic import BaseModel, Field, field_validator


class SystemModel(BaseModel):
    port: str = Field(min_length=1, max_length=20)
    scr: int = Field(ge=0, le=200)
    snd: int = Field(ge=0, le=255)
    init: int = Field(ge=0, le=1)

    @property
    def init_bool(self) -> bool:
        return bool(self.init)


class SendingCardModel(BaseModel):
    i: int = Field(ge=0, le=254)
    dvi: int
    vid: int

    @field_validator("dvi", "vid", mode="before")
    @classmethod
    def _validate_boolish(cls, value: Any) -> int:
        if isinstance(value, bool):
            return int(value)
        if value in (0, 1, "0", "1"):
            return int(value)
        raise ValueError("Value must be 0 or 1")

    @property
    def dvi_bool(self) -> bool:
        return bool(self.dvi)

    @property
    def vid_bool(self) -> bool:
        return bool(self.vid)


class ScanBoardModel(BaseModel):
    sender_index: int = Field(ge=0, le=254)
    port_index: int = Field(ge=0, le=3)
    scan_board_index: int = Field(ge=0, le=65535)
    status: str
    temperature: float | None = None
    voltage: float | None = None

    @field_validator("status", mode="before")
    @classmethod
    def _normalize_status(cls, value: str) -> str:
        if value is None:
            raise ValueError("status is required")
        normalized = value.strip().upper()
        mapping = {"OK": "OK", "E": "Error", "U": "Unknown", "ERROR": "Error", "UNKNOWN": "Unknown"}
        if normalized not in mapping:
            raise ValueError("status must be OK, E o U")
        return mapping[normalized]


class MonitorPayload(BaseModel):
    ts: datetime
    sys: SystemModel
    snds: List[SendingCardModel]
    bds: List[ScanBoardModel]

    @field_validator("bds", mode="before")
    @classmethod
    def _expand_scanboards(cls, value: Any) -> Any:
        if not isinstance(value, list):
            raise ValueError("bds must be a list")
        converted: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, list):
                if len(item) != 6:
                    raise ValueError("Each scan board entry must have 6 elements")
                converted.append(
                    {
                        "sender_index": item[0],
                        "port_index": item[1],
                        "scan_board_index": item[2],
                        "status": item[3],
                        "temperature": item[4],
                        "voltage": item[5],
                    }
                )
            elif isinstance(item, dict):
                converted.append(item)
            else:
                raise ValueError("Each scan board entry must be a list or object")
        return converted

    @field_validator("snds", mode="before")
    @classmethod
    def _ensure_list(cls, value: Any) -> Any:
        if isinstance(value, list):
            return value
        raise ValueError("snds must be a list")

    model_config = {"extra": "forbid"}
