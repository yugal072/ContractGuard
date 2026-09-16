from database.connection import SessionLocal
# AGENTS.md gotcha: import all 4 model modules so SQLAlchemy mappers register
import models.contract, models.contract_version, models.consumer, models.consumer_dependency
from models.contract import Contract
from models.contract_version import ContractVersion
from models.consumer import Consumer
from models.consumer_dependency import ConsumerDependency

db = SessionLocal()
try:
    print("=== CONTRACTS ===")
    for c in db.query(Contract).all():
        print(f"ID: {c.id}\nName: {c.name}\n")

    print("=== VERSIONS ===")
    for v in db.query(ContractVersion).all():
        print(f"ID: {v.id}\nVersion: {v.version}\nContract: {v.contract.name}\n")

    print("=== CONSUMERS ===")
    for c in db.query(Consumer).all():
        print(f"ID: {c.id}\nName: {c.name}\nType: {c.type}\nCriticality: {c.criticality}\n")

    print("=== DEPENDENCIES ===")
    for d in db.query(ConsumerDependency).all():
        print(f"Consumer: {d.consumer.name}\nContract: {d.contract_version.contract.name}")
        print(f"Endpoint: {d.endpoint}\nField: {d.field}\nUsage: {d.usage_description}\n")
finally:
    db.close()