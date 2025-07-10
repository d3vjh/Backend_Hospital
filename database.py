from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ CONEXIÓN 1: Base de datos CENTRAL (en la nube)
CENTRAL_DATABASE_URL = os.getenv("CENTRAL_DATABASE_URL")
central_engine = create_engine(CENTRAL_DATABASE_URL, echo=True)
CentralSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=central_engine)

# ✅ CONEXIÓN 2: Base de datos DEPARTAMENTO (local)
DEPT_DATABASE_URL = os.getenv("DEPT_DATABASE_URL")
dept_engine = create_engine(DEPT_DATABASE_URL, echo=True)
DeptSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dept_engine)

# Bases para modelos
CentralBase = declarative_base()
DeptBase = declarative_base()

# Dependencies
def get_central_db():
    db = CentralSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_dept_db():
    db = DeptSessionLocal()
    try:
        yield db
    finally:
        db.close()