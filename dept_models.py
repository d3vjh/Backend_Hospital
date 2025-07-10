from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Text, Enum, Numeric, Boolean, JSON, Time
from sqlalchemy.orm import relationship
from database import DeptBase
import enum

# Enums para BD Departamento
class EstadoEmpleado(enum.Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    VACACIONES = "VACACIONES"
    LICENCIA = "LICENCIA"

class EstadoCita(enum.Enum):
    PROGRAMADA = "PROGRAMADA"
    CONFIRMADA = "CONFIRMADA"
    EN_CURSO = "EN_CURSO"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"
    NO_ASISTIO = "NO_ASISTIO"

class EstadoEquipo(enum.Enum):
    OPERATIVO = "OPERATIVO"
    MANTENIMIENTO = "MANTENIMIENTO"
    FUERA_SERVICIO = "FUERA_SERVICIO"
    REPARACION = "REPARACION"

# Modelos de BD Departamento
class Departamento(DeptBase):
    __tablename__ = "departamento"
    
    id_dept = Column(Integer, primary_key=True)
    nom_dept = Column(String(100), nullable=False)
    ubicacion = Column(String(200))
    tipo_especialidad = Column(String(100))
    telefono_dept = Column(String(20))
    email_dept = Column(String(100))
    horario_atencion = Column(JSON)
    configuracion_especial = Column(JSON)
    jefe_departamento = Column(String(100))
    capacidad_atencion = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class RolEmpleado(DeptBase):
    __tablename__ = "rol_empleado"
    
    id_rol = Column(Integer, primary_key=True)
    nombre_rol = Column(String(50), nullable=False)
    descripcion_rol = Column(Text)
    permisos_sistema = Column(JSON)
    nivel_acceso = Column(Integer)
    puede_prescribir = Column(Boolean)
    puede_ver_historias = Column(Boolean)
    puede_modificar_historias = Column(Boolean)
    puede_agendar_citas = Column(Boolean)
    puede_generar_reportes = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class Empleado(DeptBase):
    __tablename__ = "empleado"
    
    id_emp = Column(Integer, primary_key=True)
    nom_emp = Column(String(50), nullable=False)
    apellido_emp = Column(String(50), nullable=False)
    dir_emp = Column(String(200))
    tel_emp = Column(String(20))
    email_emp = Column(String(100))
    fecha_contratacion = Column(Date)
    fecha_nacimiento = Column(Date, nullable=False)
    cedula = Column(String(20), nullable=False, unique=True)
    estado_empleado = Column(Enum(EstadoEmpleado))
    id_dept = Column(Integer, ForeignKey("departamento.id_dept"))
    id_rol = Column(Integer, ForeignKey("rol_empleado.id_rol"))
    numero_licencia = Column(String(50))
    especialidad_medica = Column(String(100))
    universidad_titulo = Column(String(150))
    ano_graduacion = Column(Integer)
    certificaciones = Column(JSON)
    turno_preferido = Column(String(20))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # Relaciones
    departamento = relationship("Departamento")
    rol = relationship("RolEmpleado")

class TipoCita(DeptBase):
    __tablename__ = "tipo_cita"
    
    id_tipo_cita = Column(Integer, primary_key=True)
    nombre_tipo = Column(String(50), nullable=False)
    duracion_default_min = Column(Integer)
    costo_base = Column(Numeric(10,2))
    descripcion_tipo = Column(Text)
    requiere_preparacion = Column(Boolean)
    permite_urgencia = Column(Boolean)
    requiere_interconsulta = Column(Boolean)
    configuracion_especial = Column(JSON)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class Cita(DeptBase):
    __tablename__ = "cita"
    
    id_cita = Column(Integer, primary_key=True)
    cod_pac = Column(Integer, nullable=False)  # FK a hospital_central.paciente
    id_emp = Column(Integer, ForeignKey("empleado.id_emp"), nullable=False)
    id_tipo_cita = Column(Integer, ForeignKey("tipo_cita.id_tipo_cita"), nullable=False)
    id_dept = Column(Integer, ForeignKey("departamento.id_dept"), nullable=False)
    fecha_cita = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time)
    duracion_real_min = Column(Integer)
    motivo_consulta = Column(Text)
    sintomas_principales = Column(Text)
    diagnostico_preliminar = Column(Text)
    diagnostico_final = Column(Text)
    observaciones_cita = Column(Text)
    recomendaciones = Column(Text)
    requiere_seguimiento = Column(Boolean)
    fecha_seguimiento = Column(Date)
    prioridad = Column(String(20))
    estado_cita = Column(Enum(EstadoCita))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # Relaciones
    empleado = relationship("Empleado")
    tipo_cita = relationship("TipoCita")
    departamento = relationship("Departamento")

class UsuarioSistema(DeptBase):
    __tablename__ = "usuario_sistema"
    
    id_usuario = Column(Integer, primary_key=True)
    id_emp = Column(Integer, ForeignKey("empleado.id_emp"), unique=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(100), nullable=False)
    fecha_creacion = Column(DateTime)
    ultimo_acceso = Column(DateTime)
    intentos_fallidos = Column(Integer)
    cuenta_activa = Column(Boolean)
    token_recuperacion = Column(String(255))
    token_expiracion = Column(DateTime)
    configuracion_usuario = Column(JSON)
    preferencias_interfaz = Column(JSON)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # Relaciones
    empleado = relationship("Empleado")