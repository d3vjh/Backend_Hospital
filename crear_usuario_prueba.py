# crear_usuarios_multiples.py
# Ejecutar: python crear_usuarios_multiples.py

from database import get_dept_db
from dept_models import Empleado, RolEmpleado, Departamento, UsuarioSistema
from auth import hash_password
from datetime import datetime, date
import secrets

def crear_roles_base():
    """Crear roles básicos del sistema"""
    db = next(get_dept_db())
    
    roles_base = [
        {
            "nombre_rol": "DIRECTOR",
            "descripcion_rol": "Director del hospital con todos los permisos",
            "nivel_acceso": 4,
            "permisos_sistema": {
                "puede_prescribir": True,
                "puede_ver_historias": True,
                "puede_modificar_historias": True,
                "puede_agendar_citas": True,
                "puede_generar_reportes": True,
                "es_administrador": True,
                "puede_gestionar_empleados": True,
                "puede_ver_finanzas": True
            }
        },
        {
            "nombre_rol": "MEDICO_ESPECIALISTA",
            "descripcion_rol": "Médico especialista con permisos completos de atención",
            "nivel_acceso": 3,
            "permisos_sistema": {
                "puede_prescribir": True,
                "puede_ver_historias": True,
                "puede_modificar_historias": True,
                "puede_agendar_citas": True,
                "puede_generar_reportes": True,
                "es_administrador": False,
                "puede_gestionar_empleados": False,
                "puede_ver_finanzas": False
            }
        },
        {
            "nombre_rol": "MEDICO_GENERAL",
            "descripcion_rol": "Médico general con permisos de atención básica",
            "nivel_acceso": 3,
            "permisos_sistema": {
                "puede_prescribir": True,
                "puede_ver_historias": True,
                "puede_modificar_historias": True,
                "puede_agendar_citas": True,
                "puede_generar_reportes": False,
                "es_administrador": False,
                "puede_gestionar_empleados": False,
                "puede_ver_finanzas": False
            }
        },
        {
            "nombre_rol": "ENFERMERO",
            "descripcion_rol": "Enfermero con permisos de apoyo médico",
            "nivel_acceso": 2,
            "permisos_sistema": {
                "puede_prescribir": False,
                "puede_ver_historias": True,
                "puede_modificar_historias": False,
                "puede_agendar_citas": True,
                "puede_generar_reportes": False,
                "es_administrador": False,
                "puede_gestionar_empleados": False,
                "puede_ver_finanzas": False
            }
        },
        {
            "nombre_rol": "ADMINISTRATIVO",
            "descripcion_rol": "Personal administrativo con acceso limitado",
            "nivel_acceso": 1,
            "permisos_sistema": {
                "puede_prescribir": False,
                "puede_ver_historias": False,
                "puede_modificar_historias": False,
                "puede_agendar_citas": True,
                "puede_generar_reportes": False,
                "es_administrador": False,
                "puede_gestionar_empleados": False,
                "puede_ver_finanzas": False
            }
        }
    ]
    
    try:
        for rol_data in roles_base:
            # Verificar si ya existe
            existing_rol = db.query(RolEmpleado).filter(
                RolEmpleado.nombre_rol == rol_data["nombre_rol"]
            ).first()
            
            if not existing_rol:
                # Crear el rol
                rol = RolEmpleado(
                    nombre_rol=rol_data["nombre_rol"],
                    descripcion_rol=rol_data["descripcion_rol"],
                    nivel_acceso=rol_data["nivel_acceso"],
                    permisos_sistema=rol_data["permisos_sistema"],
                    puede_prescribir=rol_data["permisos_sistema"]["puede_prescribir"],
                    puede_ver_historias=rol_data["permisos_sistema"]["puede_ver_historias"],
                    puede_modificar_historias=rol_data["permisos_sistema"]["puede_modificar_historias"],
                    puede_agendar_citas=rol_data["permisos_sistema"]["puede_agendar_citas"],
                    puede_generar_reportes=rol_data["permisos_sistema"]["puede_generar_reportes"]
                )
                db.add(rol)
                print(f"✅ Rol creado: {rol_data['nombre_rol']}")
            else:
                print(f"⚠️ Rol ya existe: {rol_data['nombre_rol']}")
        
        db.commit()
        print("✅ Roles base creados exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error creando roles: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def crear_departamentos_base():
    """Crear departamentos básicos"""
    db = next(get_dept_db())
    
    departamentos_base = [
        {
            "nom_dept": "Dirección General",
            "ubicacion": "Piso 5",
            "tipo_especialidad": "Administración",
            "telefono_dept": "123-0001",
            "email_dept": "direccion@hospital.com"
        },
        {
            "nom_dept": "Cardiología",
            "ubicacion": "Piso 2",
            "tipo_especialidad": "Enfermedades del corazón",
            "telefono_dept": "123-0002",
            "email_dept": "cardiologia@hospital.com"
        },
        {
            "nom_dept": "Medicina General",
            "ubicacion": "Piso 1",
            "tipo_especialidad": "Atención primaria",
            "telefono_dept": "123-0003",
            "email_dept": "medicina@hospital.com"
        },
        {
            "nom_dept": "Enfermería",
            "ubicacion": "Todos los pisos",
            "tipo_especialidad": "Cuidados de enfermería",
            "telefono_dept": "123-0004",
            "email_dept": "enfermeria@hospital.com"
        },
        {
            "nom_dept": "Administración",
            "ubicacion": "Piso 1",
            "tipo_especialidad": "Gestión administrativa",
            "telefono_dept": "123-0005",
            "email_dept": "admin@hospital.com"
        }
    ]
    
    try:
        for dept_data in departamentos_base:
            existing_dept = db.query(Departamento).filter(
                Departamento.nom_dept == dept_data["nom_dept"]
            ).first()
            
            if not existing_dept:
                dept = Departamento(**dept_data)
                db.add(dept)
                print(f"✅ Departamento creado: {dept_data['nom_dept']}")
            else:
                print(f"⚠️ Departamento ya existe: {dept_data['nom_dept']}")
        
        db.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error creando departamentos: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def crear_usuarios_demo():
    """Crear usuarios de demostración con diferentes roles"""
    db = next(get_dept_db())
    
    usuarios_demo = [
        {
            "username": "director",
            "password": "123456",
            "empleado": {
                "nom_emp": "Dr. Luis",
                "apellido_emp": "Director",
                "cedula": "DIR001",
                "email_emp": "director@hospital.com",
                "tel_emp": "300-000-0001",
                "especialidad_medica": "Administración Hospitalaria",
                "numero_licencia": "DIR001",
                "departamento": "Dirección General",
                "rol": "DIRECTOR"
            }
        },
        {
            "username": "cardiologo",
            "password": "123456",
            "empleado": {
                "nom_emp": "Dra. Ana",
                "apellido_emp": "Cardióloga",
                "cedula": "CAR001",
                "email_emp": "cardiologo@hospital.com",
                "tel_emp": "300-000-0002",
                "especialidad_medica": "Cardiología",
                "numero_licencia": "MED001",
                "departamento": "Cardiología",
                "rol": "MEDICO_ESPECIALISTA"
            }
        },
        {
            "username": "medico",
            "password": "123456",
            "empleado": {
                "nom_emp": "Dr. Carlos",
                "apellido_emp": "Médico",
                "cedula": "MED001",
                "email_emp": "medico@hospital.com",
                "tel_emp": "300-000-0003",
                "especialidad_medica": "Medicina General",
                "numero_licencia": "MED002",
                "departamento": "Medicina General",
                "rol": "MEDICO_GENERAL"
            }
        },
        {
            "username": "enfermera",
            "password": "123456",
            "empleado": {
                "nom_emp": "Enfermera María",
                "apellido_emp": "Enfermera",
                "cedula": "ENF001",
                "email_emp": "enfermera@hospital.com",
                "tel_emp": "300-000-0004",
                "especialidad_medica": "Enfermería General",
                "numero_licencia": "ENF001",
                "departamento": "Enfermería",
                "rol": "ENFERMERO"
            }
        },
        {
            "username": "admin",
            "password": "123456",
            "empleado": {
                "nom_emp": "Secretaria Laura",
                "apellido_emp": "Administrativa",
                "cedula": "ADM001",
                "email_emp": "admin@hospital.com",
                "tel_emp": "300-000-0005",
                "especialidad_medica": "Administración",
                "numero_licencia": "ADM001",
                "departamento": "Administración",
                "rol": "ADMINISTRATIVO"
            }
        }
    ]
    
    try:
        for usuario_data in usuarios_demo:
            # Buscar departamento
            departamento = db.query(Departamento).filter(
                Departamento.nom_dept == usuario_data["empleado"]["departamento"]
            ).first()
            
            if not departamento:
                print(f"❌ Departamento no encontrado: {usuario_data['empleado']['departamento']}")
                continue
            
            # Buscar rol
            rol = db.query(RolEmpleado).filter(
                RolEmpleado.nombre_rol == usuario_data["empleado"]["rol"]
            ).first()
            
            if not rol:
                print(f"❌ Rol no encontrado: {usuario_data['empleado']['rol']}")
                continue
            
            # Verificar si el empleado ya existe
            existing_emp = db.query(Empleado).filter(
                Empleado.email_emp == usuario_data["empleado"]["email_emp"]
            ).first()
            
            if existing_emp:
                print(f"⚠️ Empleado ya existe: {usuario_data['empleado']['email_emp']}")
                continue
            
            # Crear empleado
            empleado = Empleado(
                nom_emp=usuario_data["empleado"]["nom_emp"],
                apellido_emp=usuario_data["empleado"]["apellido_emp"],
                cedula=usuario_data["empleado"]["cedula"],
                email_emp=usuario_data["empleado"]["email_emp"],
                tel_emp=usuario_data["empleado"]["tel_emp"],
                fecha_contratacion=date.today(),
                fecha_nacimiento=date(1985, 1, 1),
                especialidad_medica=usuario_data["empleado"]["especialidad_medica"],
                numero_licencia=usuario_data["empleado"]["numero_licencia"],
                id_dept=departamento.id_dept,
                id_rol=rol.id_rol,
                turno_preferido="DIURNO"
            )
            
            db.add(empleado)
            db.flush()  # Para obtener el ID
            
            # Crear usuario del sistema
            usuario = UsuarioSistema(
                id_emp=empleado.id_emp,
                username=usuario_data["username"],
                password_hash=hash_password(usuario_data["password"]),
                salt=secrets.token_hex(16),
                fecha_creacion=datetime.utcnow(),
                intentos_fallidos=0,
                cuenta_activa=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(usuario)
            
            print(f"✅ Usuario creado: {usuario_data['username']} ({usuario_data['empleado']['rol']})")
        
        db.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error creando usuarios: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Ejecutar todo el proceso de creación"""
    print("🏥 CREANDO USUARIOS CON DIFERENTES ROLES")
    print("=" * 60)
    
    print("\n1️⃣ Creando roles base...")
    if not crear_roles_base():
        print("❌ Error creando roles. Saliendo...")
        return
    
    print("\n2️⃣ Creando departamentos base...")
    if not crear_departamentos_base():
        print("❌ Error creando departamentos. Saliendo...")
        return
    
    print("\n3️⃣ Creando usuarios demo...")
    if not crear_usuarios_demo():
        print("❌ Error creando usuarios. Saliendo...")
        return
    
    print("\n🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
    print("=" * 60)
    print("\n👥 USUARIOS CREADOS:")
    print("┌─────────────┬─────────────┬─────────────────────┬──────────────────────────┐")
    print("│   Usuario   │ Contraseña  │         Rol         │       Departamento       │")
    print("├─────────────┼─────────────┼─────────────────────┼──────────────────────────┤")
    print("│  director   │   123456    │      DIRECTOR       │    Dirección General     │")
    print("│ cardiologo  │   123456    │ MEDICO_ESPECIALISTA │       Cardiología        │")
    print("│   medico    │   123456    │  MEDICO_GENERAL     │    Medicina General      │")
    print("│ enfermera   │   123456    │     ENFERMERO       │       Enfermería         │")
    print("│   admin     │   123456    │  ADMINISTRATIVO     │     Administración       │")
    print("└─────────────┴─────────────┴─────────────────────┴──────────────────────────┘")
    
    print("\n🔐 PERMISOS POR ROL:")
    print("📋 DIRECTOR: Todos los permisos (gestión completa)")
    print("⚕️ MEDICO_ESPECIALISTA: Prescribir, historias, citas, reportes")
    print("🩺 MEDICO_GENERAL: Prescribir, historias, citas (sin reportes)")
    print("👩‍⚕️ ENFERMERO: Ver historias, agendar citas (no prescribir)")
    print("📝 ADMINISTRATIVO: Solo agendar citas")
    
    print("\n🚀 ¡Ya puedes probar con diferentes usuarios!")

if __name__ == "__main__":
    main()