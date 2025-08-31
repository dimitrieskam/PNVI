from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
engine = create_engine("sqlite:///snake_ladder.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    fastest_win_seconds = Column(Integer, default=9999)

def create_db():
    Base.metadata.create_all(bind=engine)
