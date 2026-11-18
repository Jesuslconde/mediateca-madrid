from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mediateca_shared.db import Base


class Lista(Base):
    """Lista de favoritos identificada por un token opaco."""

    __tablename__ = "listas"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    titulo: Mapped[str] = mapped_column(String(80), default="Mi lista", server_default="Mi lista")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    items: Mapped[list[ListaItem]] = relationship(
        back_populates="lista",
        cascade="all, delete-orphan",
        order_by="ListaItem.added_at.desc()",
    )


class ListaItem(Base):
    """Edicion guardada en una lista, con el titulo como respaldo."""

    __tablename__ = "lista_items"
    __table_args__ = (Index("ix_lista_items_lista_added", "lista_id", "added_at"),)

    lista_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("listas.id", ondelete="CASCADE"),
        primary_key=True,
    )
    record_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    titulo_snapshot: Mapped[str] = mapped_column(String(1000))
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    lista: Mapped[Lista] = relationship(back_populates="items")
