from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base,sessionmaker

DATABASE_URL = "sqlite:///scientific_network.db"

engine = create_engine(DATABASE_URL)

Sessionlocal = sessionmaker(bind=engine)

Base = declarative_base()

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()