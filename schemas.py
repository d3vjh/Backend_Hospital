from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional

# Schemas para Employee
class EmployeeBase(BaseModel):
    nom_emp: str
    apellido_emp: str
    email_emp: EmailStr
    cedula: str

class EmployeeCreate(EmployeeBase):
    password: str
    id_dept: int

class EmployeeResponse(EmployeeBase):
    id_emp: int
    estado_empleado: str
    
    class Config:
        from_attributes = True

# Schemas para Patient
class PatientBase(BaseModel):
    nom_pac: str
    apellido_pac: str
    cedula: str
    telefono: Optional[str] = None
    email_pac: Optional[EmailStr] = None
    fecha_nac: Optional[date] = None

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    cod_pac: int
    estado_paciente: str
    
    class Config:
        from_attributes = True

# Schemas para Appointment
class AppointmentBase(BaseModel):
    cod_pac: int
    id_emp: int
    fecha_cita: date
    hora_cita: str
    motivo: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentResponse(AppointmentBase):
    id_cita: int
    
    class Config:
        from_attributes = True

# Login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str