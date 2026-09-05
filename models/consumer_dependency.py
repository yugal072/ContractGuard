from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base

if TYPE_CHECKING:
    from models.consumer import Consumer
    from models.contract_version import ContractVersion


class ConsumerDependency(Base):
    __tablename__ = "consumer_dependencies"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # FK linking back to the Consumer
    consumer_id: Mapped[int] = mapped_column(
        ForeignKey("consumers.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # FK linking to the specific ContractVersion the consumer depends on
    contract_version_id: Mapped[int] = mapped_column(
        ForeignKey("contract_versions.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # The API endpoint the consumer queries (e.g., "GET /orders/{id}")
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # The specific JSON request/response field they rely on (e.g., "customer_name", "total")
    field: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Optional explanation of what the consumer does with this field
    usage_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Many-to-One relationship back to the Consumer
    consumer: Mapped["Consumer"] = relationship("Consumer", back_populates="dependencies")

    # Many-to-One relationship back to the ContractVersion
    contract_version: Mapped["ContractVersion"] = relationship("ContractVersion", back_populates="dependencies")