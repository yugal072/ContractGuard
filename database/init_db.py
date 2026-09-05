from database.connection import engine, Base

import models.contract
import models.contract_version
import models.consumer
import models.consumer_dependency

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")
    