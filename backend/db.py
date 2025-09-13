from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

ENGINE = create_engine("sqlite:///backend/wolyt.db", echo=False, future=True)
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False)
Base = declarative_base()
