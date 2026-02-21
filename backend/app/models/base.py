"""SQLAlchemy base model with common columns.

All ORM models inherit from Base, which provides:
- UUID primary key (auto-generated)
- created_at timestamp (auto-set on insert)
- updated_at timestamp (auto-set on insert and update)
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Abstract base for all Synapse database models.

    Provides id, created_at, and updated_at columns automatically.
    Subclasses just define their own table-specific columns.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )