from typing import TYPE_CHECKING
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base

if TYPE_CHECKING:
    from models.consumer_dependency import ConsumerDependency


class Consumer(Base):
    __tablename__ = "consumers"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Name of the consumer system (e.g., "Frontend Web App", "iOS App", "Billing Service")
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    
    # Type of system: "frontend", "mobile", "service", etc.
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Business impact level: "low", "medium", "high"
    criticality: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    
    # Optional detailed description of what the consumer does
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 1-to-Many relationship: One consumer has many specific API dependencies
    # Deleting a consumer cascade-deletes their dependencies
    dependencies: Mapped[list["ConsumerDependency"]] = relationship(
        "ConsumerDependency",
        back_populates="consumer",
        cascade="all, delete-orphan"
    )