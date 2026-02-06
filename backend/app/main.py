from __future__ import annotations

from datetime import datetime, timezone
from collections import defaultdict
import os

import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_session
from .models import ControlSystem, ScanBoard, SendingCard
from .schemas import MonitorPayload

logger = logging.getLogger(__name__)

app = FastAPI(title="LED Monitor Ingest API")

allowed_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
origins = [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest")
def ingest(payload: MonitorPayload, session: Session = Depends(get_session)) -> dict[str, int]:
    timestamp = payload.ts.astimezone(timezone.utc).replace(tzinfo=None)

    device_id = payload.sys.dev or payload.device_id
    if not device_id:
        raise HTTPException(status_code=422, detail="device_id is required either in sys.dev or root device_id")

    control_system = session.scalar(select(ControlSystem).where(ControlSystem.device_id == device_id))
    if control_system is None:
        control_system = ControlSystem(
            device_id=device_id,
            com_port=payload.sys.port,
            global_brightness=payload.sys.bri,
            screen_count=payload.sys.scr,
            sender_count=payload.sys.snd,
            is_initialized=payload.sys.init_bool,
            last_update=timestamp,
        )
        session.add(control_system)
        session.flush()
    else:
        control_system.device_id = device_id
        control_system.com_port = payload.sys.port
        control_system.global_brightness = payload.sys.bri
        control_system.screen_count = payload.sys.scr
        control_system.sender_count = payload.sys.snd
        control_system.is_initialized = payload.sys.init_bool
        control_system.last_update = timestamp

    # Replace sending cards snapshot
    session.query(SendingCard).filter_by(control_system_id=control_system.id).delete(synchronize_session=False)
    unique_senders: dict[int, SendingCard] = {}
    for card in payload.snds:
        unique_senders[card.i] = SendingCard(
            control_system_id=control_system.id,
            device_id=device_id,
            sender_index=card.i,
            dvi_status=card.dvi_bool,
            is_video_ok=card.vid_bool,
            last_update=timestamp,
        )
    sending_rows = list(unique_senders.values())
    if len(sending_rows) < len(payload.snds):
        logger.info(
            "Deduplicated sending cards for device_id=%s: %s -> %s entries",
            device_id,
            len(payload.snds),
            len(sending_rows),
        )
    session.add_all(sending_rows)

    # Replace scan board snapshot
    session.query(ScanBoard).filter_by(control_system_id=control_system.id).delete(synchronize_session=False)
    unique_boards: dict[tuple[int, int, int], ScanBoard] = {}
    for board in payload.bds:
        key = (board.sender_index, board.port_index, board.scan_board_index)
        unique_boards[key] = ScanBoard(
            control_system_id=control_system.id,
            device_id=device_id,
            sender_index=board.sender_index,
            port_index=board.port_index,
            scan_board_index=board.scan_board_index,
            status=board.status,
            temperature=board.temperature,
            voltage=board.voltage,
            last_update=timestamp,
        )
    scan_rows = list(unique_boards.values())
    if len(scan_rows) < len(payload.bds):
        logger.info(
            "Deduplicated scan boards for device_id=%s: %s -> %s entries",
            device_id,
            len(payload.bds),
            len(scan_rows),
        )
    session.add_all(scan_rows)

    try:
        session.commit()
    except Exception as exc:  # pragma: no cover - defensive rollback
        session.rollback()
        logger.exception("Failed to persist payload for device_id=%s", device_id)
        raise HTTPException(status_code=500, detail="Failed to persist payload") from exc

    return {
        "control_system_id": control_system.id,
        "sending_cards": len(sending_rows),
        "scan_boards": len(scan_rows),
    }


@app.get("/monitor/{device_id}")
def get_monitor(device_id: str, session: Session = Depends(get_session)) -> dict[str, object]:
    control_system = session.scalar(select(ControlSystem).where(ControlSystem.device_id == device_id))
    if control_system is None:
        raise HTTPException(status_code=404, detail="device_id not found")

    sending_cards = session.scalars(
        select(SendingCard).where(SendingCard.control_system_id == control_system.id).order_by(SendingCard.sender_index)
    ).all()
    scan_boards = session.scalars(
        select(ScanBoard)
        .where(ScanBoard.control_system_id == control_system.id)
        .order_by(ScanBoard.sender_index, ScanBoard.port_index, ScanBoard.scan_board_index)
    ).all()

    return _snapshot_payload(control_system, sending_cards, scan_boards)


@app.get("/monitors")
def list_monitors(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    control_systems = session.scalars(select(ControlSystem).order_by(ControlSystem.device_id)).all()
    if not control_systems:
        return []

    control_ids = [cs.id for cs in control_systems]
    if not control_ids:
        return []

    sending_cards = session.scalars(
        select(SendingCard).where(SendingCard.control_system_id.in_(control_ids)).order_by(SendingCard.control_system_id, SendingCard.sender_index)
    ).all()
    scan_boards = session.scalars(
        select(ScanBoard)
        .where(ScanBoard.control_system_id.in_(control_ids))
        .order_by(ScanBoard.control_system_id, ScanBoard.sender_index, ScanBoard.port_index, ScanBoard.scan_board_index)
    ).all()

    send_by_control = defaultdict(list)
    for card in sending_cards:
        send_by_control[card.control_system_id].append(card)

    scan_by_control = defaultdict(list)
    for board in scan_boards:
        scan_by_control[board.control_system_id].append(board)

    return [
        _snapshot_payload(cs, send_by_control.get(cs.id, []), scan_by_control.get(cs.id, []))
        for cs in control_systems
    ]


def _format_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).isoformat()
    return value.astimezone(timezone.utc).isoformat()


def _status_short(status: str | None) -> str:
    mapping = {"OK": "OK", "Error": "E", "Unknown": "U"}
    if status is None:
        return "U"
    return mapping.get(status, "U")


def _snapshot_payload(
    control_system: ControlSystem, sending_cards: list[SendingCard], scan_boards: list[ScanBoard]
) -> dict[str, object]:
    return {
        "device_id": control_system.device_id,
        "ts": _format_timestamp(control_system.last_update),
        "sys": {
            "port": control_system.com_port,
            "bri": control_system.global_brightness,
            "scr": control_system.screen_count or 0,
            "snd": control_system.sender_count or 0,
            "init": 1 if control_system.is_initialized else 0,
        },
        "snds": [
            {
                "i": card.sender_index,
                "dvi": 1 if card.dvi_status else 0,
                "vid": 1 if card.is_video_ok else 0,
                "last_update": _format_timestamp(card.last_update),
            }
            for card in sending_cards
        ],
        "bds": [
            [
                board.sender_index,
                board.port_index,
                board.scan_board_index,
                _status_short(board.status),
                board.temperature,
                board.voltage,
            ]
            for board in scan_boards
        ],
    }
