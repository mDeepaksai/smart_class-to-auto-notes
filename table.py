from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func
from database_model import Base

class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(100), nullable=False)
    title = Column(String(150))
    transcript = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())