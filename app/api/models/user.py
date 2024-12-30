from sqlalchemy import Column, Integer, String
from config.database import Base
from pydantic import BaseModel
from typing import Optional

# Modelo para la base de datos
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    age = Column(Integer)

# Modelo para la API (Pydantic)
class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    age: int