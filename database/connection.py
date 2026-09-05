import os
from dotenv  import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# load variables 
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not defined.")

# create sqlalchemy engine 
engine = create_engine(DATABASE_URL)

# create the sessionlocal class
SessionLocal = sessionmaker(autoflush=False, autocommit= False, bind=engine)

# expose declarative base
Base = declarative_base()