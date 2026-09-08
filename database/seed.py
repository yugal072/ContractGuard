from database.connection import SessionLocal
from models.contract import Contract
from models.contract_version import ContractVersion
from models.consumer import Consumer
from models.consumer_dependency import ConsumerDependency
from datetime import datetime


def seed():
    session = SessionLocal()
    try:
        # --- Contract ---
        contract = Contract(name="Order API", description="Order management API")
        session.add(contract)
        session.flush()  # get contract.id

        # --- Versions ---
        v1 = ContractVersion(
            contract_id=contract.id, version="v1",
            status="released", source="registered",
            spec="openapi: 3.0.0\ninfo:\n  title: Order API\n  version: v1"
        )
        v2 = ContractVersion(
            contract_id=contract.id, version="v2",
            status="approved", source="registered",
            spec="openapi: 3.0.0\ninfo:\n  title: Order API\n  version: v2"
        )
        v3 = ContractVersion(
            contract_id=contract.id, version="v3",
            status="draft", source="registered",
            spec="openapi: 3.0.0\ninfo:\n  title: Order API\n  version: v3"
        )
        session.add_all([v1, v2, v3])
        session.flush()

        # --- Consumers ---
        frontend = Consumer(name="Frontend", type="frontend", criticality="high",
                            description="Web frontend application")
        mobile   = Consumer(name="Mobile", type="mobile", criticality="medium",
                            description="Mobile application")
        billing  = Consumer(name="Billing", type="service", criticality="high",
                            description="Billing service")
        session.add_all([frontend, mobile, billing])
        session.flush()

        # --- Dependencies ---
        deps = [
            ConsumerDependency(consumer_id=frontend.id, contract_version_id=v1.id,
                               endpoint="GET /orders/{id}", field="customer_name",
                               usage_description="Display customer name on order page"),
            ConsumerDependency(consumer_id=frontend.id, contract_version_id=v1.id,
                               endpoint="GET /orders/{id}", field="order_id",
                               usage_description="Display order ID on order page"),
            ConsumerDependency(consumer_id=mobile.id, contract_version_id=v2.id,
                               endpoint="GET /orders/{id}", field="customer_name",
                               usage_description="Show customer name in mobile order view"),
            ConsumerDependency(consumer_id=mobile.id, contract_version_id=v2.id,
                               endpoint="GET /orders/{id}", field="status",
                               usage_description="Show order status badge"),
            ConsumerDependency(consumer_id=mobile.id, contract_version_id=v2.id,
                               endpoint="GET /purchase", field="amount",
                               usage_description="Display purchase amount"),
            ConsumerDependency(consumer_id=billing.id, contract_version_id=v2.id,
                               endpoint="GET /orders/{id}", field="total",
                               usage_description="Calculate invoice total"),
        ]
        session.add_all(deps)

        session.commit()
        print("Seed data inserted successfully.")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()