from sqlalchemy import Column, Integer, String, Text
from database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)

    date = Column(String, nullable=True)

    time = Column(String, nullable=True)

    priority = Column(String, nullable=False)

    reason = Column(Text, nullable=True)

    status = Column(String, default="pending")