from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
db_url="mysql+pymysql://root:deeps%40simi@localhost:3306/smartclassroom"
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()