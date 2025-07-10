from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Text, Enum, Numeric, Boolean, JSON
from sqlalchemy.orm import relationship
from database import CentralBase
import enum

# Enums para BD Central
class EstadoPaciente(enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    FALLECIDO = "FALLECIDO"
    TRANSFERIDO = "TRANSFERIDO"

class GeneroEnum(enum.Enum):
    M = "M"
    F = "F"
    OTRO = "OTRO"

class EstadoHistoria(enum.Enum):
    ACTIVA = "ACTIVA"
    CERRADA = "CERRADA"
    ARCHIVADA = "ARCHIVADA"

class EstadoMedicamento(enum.Enum):
    DISPONIBLE = "DISPONIBLE"
    AGOTADO = "AGOTADO"
    VENCIDO = "VENCIDO"
    RETIRADO = "RETIRADO"

# Modelos de BD Central
class TipoSangre(CentralBase):
    __tablename__ = "tipo_sangre"
    
    id_tipo_sangre = Column(Integer, primary_key=True)
    tipo_sangre = Column(String(5), nullable=False, unique=True)
    descripcion = Column(String(100))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class DepartamentoMaster(CentralBase):
    __tablename__ = "departamento_master"
    
    id_dept = Column(Integer, primary_key=True)
    nom_dept = Column(String(100), nullable=False)
    tipo_especialidad = Column(String(100))
    ubicacion = Column(String(200))
    telefono_dept = Column(String(20))
    email_dept = Column(String(100))
    database_name = Column(String(50))
    servidor_host = Column(String(100))
    servidor_puerto = Column(Integer)
    estado_departamento = Column(String(20))
    fecha_creacion = Column(Date)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class Paciente(CentralBase):
    __tablename__ = "paciente"
    
    cod_pac = Column(Integer, primary_key=True)
    nom_pac = Column(String(50), nullable=False)
    apellido_pac = Column(String(50), nullable=False)
    dir_pac = Column(String(200))
    tel_pac = Column(String(20))
    email_pac = Column(String(100))
    fecha_nac = Column(Date, nullable=False)
    genero = Column(Enum(GeneroEnum))
    cedula = Column(String(20), nullable=False, unique=True)
    num_seguro = Column(String(50))
    id_tipo_sangre = Column(Integer, ForeignKey("tipo_sangre.id_tipo_sangre"))
    estado_paciente = Column(Enum(EstadoPaciente))
    departamentos_atencion = Column(JSON)
    id_dept_principal = Column(Integer, ForeignKey("departamento_master.id_dept"))
    fecha_ultima_atencion = Column(Date)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # Relaciones
    tipo_sangre = relationship("TipoSangre")
    departamento_principal = relationship("DepartamentoMaster")

class HistoriaClinica(CentralBase):
    __tablename__ = "historia_clinica"
    
    cod_hist = Column(Integer, primary_key=True)
    cod_pac = Column(Integer, ForeignKey("paciente.cod_pac"), nullable=False)
    fecha_creacion = Column(Date)
    observaciones_generales = Column(Text)
    peso_kg = Column(Numeric(5,2))
    altura_cm = Column(Numeric(5,2))
    alergias_conocidas = Column(Text)
    antecedentes_familiares = Column(Text)
    antecedentes_personales = Column(Text)
    id_dept_origen = Column(Integer, ForeignKey("departamento_master.id_dept"))
    departamentos_acceso = Column(JSON)
    confidencial = Column(Boolean)
    estado_historia = Column(Enum(EstadoHistoria))
    fecha_ultima_modificacion = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # Relaciones
    paciente = relationship("Paciente")
    departamento_origen = relationship("DepartamentoMaster")

class Medicamento(CentralBase):
    __tablename__ = "medicamento"
    
    cod_med = Column(Integer, primary_key=True)
    nom_med = Column(String(100), nullable=False)
    principio_activo = Column(String(200), nullable=False)
    descripcion_med = Column(Text)
    concentracion = Column(String(50))
    forma_farmaceutica = Column(String(50))
    stock_actual = Column(Integer)
    stock_minimo = Column(Integer)
    stock_maximo = Column(Integer)
    precio_unitario = Column(Numeric(10,2))
    precio_compra = Column(Numeric(10,2))
    fecha_vencimiento = Column(Date)
    estado_medicamento = Column(Enum(EstadoMedicamento))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Laboratorio(CentralBase):
    __tablename__ = "laboratorio"
    
    id_laboratorio = Column(Integer, primary_key=True)
    nombre_laboratorio = Column(String(100), nullable=False)
    telefono_lab = Column(String(20))
    email_lab = Column(String(100))
    pais_origen = Column(String(50))
    certificacion_fda = Column(Boolean)
    certificacion_invima = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class CategoriaMedicamento(CentralBase):
    __tablename__ = "categoria_medicamento"
    
    id_categoria = Column(Integer, primary_key=True)
    nombre_categoria = Column(String(50), nullable=False)
    descripcion_categoria = Column(Text)
    requiere_receta = Column(Boolean)
    medicamento_controlado = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

# En la clase Medicamento, agregar estas líneas al final:
id_laboratorio = Column(Integer, ForeignKey("laboratorio.id_laboratorio"))
id_categoria = Column(Integer, ForeignKey("categoria_medicamento.id_categoria"))

# Relaciones (agregar al final de la clase)
laboratorio = relationship("Laboratorio")
categoria = relationship("CategoriaMedicamento")