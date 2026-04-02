import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

db_url = os.environ.get("DATABASE_URL", "")

engine = create_engine(
    db_url,
    connect_args={"ssl": {"fake_flag_to_enable_ssl": True}}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()