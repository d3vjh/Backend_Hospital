from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Text, Enum
from sqlalchemy.orm import relationship
from database import Base
import enum

# Enums básicos
class EstadoEmpleado(enum.Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"

class EstadoPaciente(enum.Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"

# Modelos principales
class Department(Base):
    __tablename__ = "departamentos"
    id_dept = Column(Integer, primary_key=True)
    nom_dept = Column(String(100), nullable=False)
    ubicacion = Column(String(200))

class Employee(Base):
    __tablename__ = "empleados"
    id_emp = Column(Integer, primary_key=True)
    nom_emp = Column(String(100), nullable=False)
    apellido_emp = Column(String(100), nullable=False)
    email_emp = Column(String(100), unique=True)
    cedula = Column(String(20), unique=True)
    password_hash = Column(String(255))
    estado_empleado = Column(Enum(EstadoEmpleado), default=EstadoEmpleado.ACTIVO)
    id_dept = Column(Integer, ForeignKey("departamentos.id_dept"))
    
    departamento = relationship("Department")

class Patient(Base):
    __tablename__ = "pacientes"
    cod_pac = Column(Integer, primary_key=True)
    nom_pac = Column(String(100), nullable=False)
    apellido_pac = Column(String(100), nullable=False)
    cedula = Column(String(20), unique=True)
    telefono = Column(String(20))
    email_pac = Column(String(100))
    fecha_nac = Column(Date)
    estado_paciente = Column(Enum(EstadoPaciente), default=EstadoPaciente.ACTIVO)

class Appointment(Base):
    __tablename__ = "citas"
    id_cita = Column(Integer, primary_key=True)
    cod_pac = Column(Integer, ForeignKey("pacientes.cod_pac"))
    id_emp = Column(Integer, ForeignKey("empleados.id_emp"))
    fecha_cita = Column(Date, nullable=False)
    hora_cita = Column(String(10))
    motivo = Column(Text)
    
    paciente = relationship("Patient")
    empleado = relationship("Employee")

class Medication(Base):
    __tablename__ = "medicamentos"
    cod_med = Column(Integer, primary_key=True)
    nom_med = Column(String(100), nullable=False)
    descripcion = Column(Text)
    stock_actual = Column(Integer, default=0)
    precio = Column(String(20))