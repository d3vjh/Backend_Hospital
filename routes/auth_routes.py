from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Employee
from schemas import LoginRequest
from auth import verify_password, create_access_token

router = APIRouter()

@router.post("/login")
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    # Buscar empleado por email
    employee = db.query(Employee).filter(Employee.email_emp == login_data.email).first()
    
    if not employee or not verify_password(login_data.password, employee.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    access_token = create_access_token(data={"sub": str(employee.id_emp)})
    return {"access_token": access_token, "token_type": "bearer"}