import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
load_dotenv()
url=os.getenv("DATABASE_URL","").strip()
if not url: raise RuntimeError("Set DATABASE_URL in .env")
if url.startswith("postgres://"): url=url.replace("postgres://","postgresql+psycopg://",1)
elif url.startswith("postgresql://"): url=url.replace("postgresql://","postgresql+psycopg://",1)
engine=create_engine(url,pool_pre_ping=True)
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
class Base(DeclarativeBase): pass
def get_db():
    db=SessionLocal()
    try: yield db
    finally: db.close()
