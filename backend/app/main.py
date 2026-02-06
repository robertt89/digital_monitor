from __future__ import annotations

from datetime import timezone

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_session
from .models import ControlSystem, ScanBoard, SendingCard
from .schemas import MonitorPayload

app = FastAPI(title="LED Monitor Ingest API")


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
        control_system.screen_count = payload.sys.scr
        control_system.sender_count = payload.sys.snd
        control_system.is_initialized = payload.sys.init_bool
        control_system.last_update = timestamp

    # Replace sending cards snapshot
    session.query(SendingCard).filter_by(control_system_id=control_system.id).delete(synchronize_session=False)
    sending_rows = [
        SendingCard(
            control_system_id=control_system.id,
            device_id=device_id,
            sender_index=card.i,
            dvi_status=card.dvi_bool,
            is_video_ok=card.vid_bool,
            last_update=timestamp,
        )
        for card in payload.snds
    ]
    session.add_all(sending_rows)

    # Replace scan board snapshot
    session.query(ScanBoard).filter_by(control_system_id=control_system.id).delete(synchronize_session=False)
    scan_rows = [
        ScanBoard(
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
        for board in payload.bds
    ]
    session.add_all(scan_rows)

    try:
        session.commit()
    except Exception as exc:  # pragma: no cover - defensive rollback
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to persist payload") from exc

    return {
        "control_system_id": control_system.id,
        "sending_cards": len(sending_rows),
        "scan_boards": len(scan_rows),
    }
