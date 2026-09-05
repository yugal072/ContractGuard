from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base

if TYPE_CHECKING:
    from models.contract import Contract
    from models.consumer_dependency import ConsumerDependency
    
class ContractVersion(Base):
    __tablename__ = "contract_versions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    # foreign key referencing the parent contract. 
    # Cascade deletes if contract is deleted
    contract_id: Mapped[int] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable= False
    )
    
    # version identifier 
    version: Mapped[str] = mapped_column(String(50), nullable=True)
    
    #status: draft, approved, released
    status: Mapped[str] = mapped_column(String(50), nullable=False,default="draft")
    
    #source: git, registered
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # spec: raw openapi specification
    spec: Mapped[str] = mapped_column(Text, nullable=False)
    
    # creation timestamp 
    created_at: Mapped[datetime]= mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # many to one relation back to parent contract
    contract: Mapped["Contract"] = relationship("Contract", back_populates="versions")
    
    # 1 to many for multiple consumer and then consumer dependencies
    dependencies: Mapped[list["ConsumerDependency"]] = relationship(
        "ConsumerDependency",
        back_populates="contract_version",
        cascade="all, delete-orphan"
    )
    