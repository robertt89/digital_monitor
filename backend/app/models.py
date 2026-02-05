from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, SmallInteger, String, TIMESTAMP, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ControlSystem(Base):
    __tablename__ = "control_system"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    com_port: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    screen_count: Mapped[int | None]
    sender_count: Mapped[int | None]
    is_initialized: Mapped[bool] = mapped_column(Boolean, default=False)
    last_update: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )

    sending_cards: Mapped[list[SendingCard]] = relationship(back_populates="control_system", cascade="all, delete-orphan")
    scan_boards: Mapped[list[ScanBoard]] = relationship(back_populates="control_system", cascade="all, delete-orphan")


class SendingCard(Base):
    __tablename__ = "sending_card"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    control_system_id: Mapped[int] = mapped_column(ForeignKey("control_system.id", ondelete="CASCADE"), nullable=False)
    sender_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    dvi_status: Mapped[bool | None] = mapped_column(Boolean)
    is_video_ok: Mapped[bool | None] = mapped_column(Boolean)
    last_update: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )

    control_system: Mapped[ControlSystem] = relationship(back_populates="sending_cards")


class ScanBoard(Base):
    __tablename__ = "scan_board"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    control_system_id: Mapped[int] = mapped_column(ForeignKey("control_system.id", ondelete="CASCADE"), nullable=False)
    sender_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    port_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    scan_board_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(Enum("OK", "Error", "Unknown"), default="Unknown", nullable=False)
    temperature: Mapped[float | None] = mapped_column(Float)
    voltage: Mapped[float | None] = mapped_column(Float)
    last_update: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )

    control_system: Mapped[ControlSystem] = relationship(back_populates="scan_boards")
