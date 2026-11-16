from datetime import datetime, timezone
from sqlalchemy import String,Integer,DateTime,ForeignKey,Boolean
from sqlalchemy.orm import Mapped,mapped_column,relationship
from .db import Base
def now(): return datetime.now(timezone.utc)
class Clinic(Base):
    __tablename__="clinics"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(140))
    slug:Mapped[str]=mapped_column(String(80),unique=True,index=True)
    city:Mapped[str]=mapped_column(String(100),default="")
    phone:Mapped[str]=mapped_column(String(40),default="")
    active:Mapped[bool]=mapped_column(Boolean,default=True)
class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(primary_key=True)
    clinic_id:Mapped[int]=mapped_column(ForeignKey("clinics.id"))
    name:Mapped[str]=mapped_column(String(120))
    email:Mapped[str]=mapped_column(String(190),unique=True,index=True)
    password_hash:Mapped[str]=mapped_column(String(300))
class Token(Base):
    __tablename__="tokens"
    id:Mapped[int]=mapped_column(primary_key=True)
    clinic_id:Mapped[int]=mapped_column(ForeignKey("clinics.id"),index=True)
    number:Mapped[int]=mapped_column(Integer)
    patient:Mapped[str]=mapped_column(String(120))
    phone:Mapped[str]=mapped_column(String(40),default="")
    status:Mapped[str]=mapped_column(String(20),default="Waiting")
    created:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
