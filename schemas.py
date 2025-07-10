from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import date, datetime
from enum import Enum

# ===============================================
# SCHEMA SIMPLE PARA PACIENTES (SIN VALIDACIONES COMPLEJAS)
# ===============================================
class PatientCreate(BaseModel):
    nom_pac: str
    apellido_pac: str
    cedula: str
    fecha_nac: Optional[str] = None  # ← Cambiar a string por ahora
    genero: Optional[str] = None
    email_pac: Optional[str] = None
    tel_pac: Optional[str] = None
    dir_pac: Optional[str] = None
    num_seguro: Optional[str] = None
    id_tipo_sangre: Optional[int] = None
    id_dept_principal: Optional[int] = None

class PatientUpdate(BaseModel):
    nom_pac: Optional[str] = None
    apellido_pac: Optional[str] = None
    cedula: Optional[str] = None
    fecha_nac: Optional[str] = None  # ← String por ahora
    genero: Optional[str] = None
    email_pac: Optional[str] = None
    tel_pac: Optional[str] = None
    dir_pac: Optional[str] = None
    num_seguro: Optional[str] = None
    estado_paciente: Optional[str] = None
    id_tipo_sangre: Optional[int] = None
    id_dept_principal: Optional[int] = None


class PatientResponse(BaseModel):
    cod_pac: int
    nom_pac: str
    apellido_pac: str
    dir_pac: Optional[str] = None
    tel_pac: Optional[str] = None
    email_pac: Optional[str] = None
    fecha_nac: Optional[date] = None
    genero: Optional[str] = None
    cedula: str
    num_seguro: Optional[str] = None
    estado_paciente: Optional[str] = None
    departamentos_atencion: Optional[Any] = None
    id_tipo_sangre: Optional[int] = None
    id_dept_principal: Optional[int] = None
    fecha_ultima_atencion: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        # Esto permite que Pydantic convierta automáticamente los enums a strings
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None,
        }

# ===============================================
# SCHEMAS AUXILIARES
# ===============================================
class MessageResponse(BaseModel):
    message: str

class CountResponse(BaseModel):
    total: int