from database import get_central_db, get_dept_db, central_engine, dept_engine
from central_models import Paciente, DepartamentoMaster, TipoSangre
from dept_models import Empleado, Departamento, RolEmpleado
from sqlalchemy.orm import Session
from sqlalchemy import text  # ← AGREGAR ESTA IMPORTACIÓN

def test_central_connection():
    """Probar conexión a BD Central"""
    print("🔍 Probando conexión a BD CENTRAL...")
    
    try:
        # Probar conexión básica
        with central_engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))  # ← USAR text()
            print("✅ Conexión a BD Central: OK")
        
        # Probar con sessión
        db = next(get_central_db())
        
        # Contar registros en tablas principales
        pacientes_count = db.query(Paciente).count()
        departamentos_count = db.query(DepartamentoMaster).count()
        tipos_sangre_count = db.query(TipoSangre).count()
        
        print(f"📊 BD Central - Registros encontrados:")
        print(f"   - Pacientes: {pacientes_count}")
        print(f"   - Departamentos: {departamentos_count}")
        print(f"   - Tipos de sangre: {tipos_sangre_count}")
        
        # Mostrar algunos pacientes
        if pacientes_count > 0:
            pacientes = db.query(Paciente).limit(3).all()
            print(f"📋 Primeros pacientes:")
            for p in pacientes:
                print(f"   - {p.nom_pac} {p.apellido_pac} (ID: {p.cod_pac})")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en BD Central: {e}")
        return False

def test_dept_connection():
    """Probar conexión a BD Departamento"""
    print("\n🔍 Probando conexión a BD DEPARTAMENTO...")
    
    try:
        # Probar conexión básica
        with dept_engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))  # ← USAR text()
            print("✅ Conexión a BD Departamento: OK")
        
        # Probar con sessión
        db = next(get_dept_db())
        
        # Contar registros en tablas principales
        empleados_count = db.query(Empleado).count()
        departamentos_count = db.query(Departamento).count()
        roles_count = db.query(RolEmpleado).count()
        
        print(f"📊 BD Departamento - Registros encontrados:")
        print(f"   - Empleados: {empleados_count}")
        print(f"   - Departamentos: {departamentos_count}")
        print(f"   - Roles: {roles_count}")
        
        # Mostrar algunos empleados
        if empleados_count > 0:
            empleados = db.query(Empleado).limit(3).all()
            print(f"👥 Primeros empleados:")
            for e in empleados:
                print(f"   - {e.nom_emp} {e.apellido_emp} (ID: {e.id_emp})")
        
        # Mostrar roles disponibles
        if roles_count > 0:
            roles = db.query(RolEmpleado).all()
            print(f"🔒 Roles disponibles:")
            for r in roles:
                print(f"   - {r.nombre_rol}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en BD Departamento: {e}")
        return False

def test_cross_database_query():
    """Probar consulta que cruza ambas bases de datos"""
    print("\n🔗 Probando consulta cruzada...")
    
    try:
        # BD Central
        central_db = next(get_central_db())
        # BD Departamento  
        dept_db = next(get_dept_db())
        
        # Obtener un paciente de central
        paciente = central_db.query(Paciente).first()
        
        if paciente:
            print(f"📋 Paciente en Central: {paciente.nom_pac} {paciente.apellido_pac}")
            
            # Buscar empleados que podrían atenderlo
            empleados = dept_db.query(Empleado).filter(
                Empleado.estado_empleado == "ACTIVO"
            ).limit(3).all()
            
            print(f"👨‍⚕️ Empleados disponibles para atender:")
            for emp in empleados:
                print(f"   - Dr. {emp.nom_emp} {emp.apellido_emp}")
        
        central_db.close()
        dept_db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en consulta cruzada: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 INICIANDO PRUEBAS DE CONEXIÓN")
    print("=" * 50)
    
    # Test 1: BD Central
    central_ok = test_central_connection()
    
    # Test 2: BD Departamento
    dept_ok = test_dept_connection()
    
    # Test 3: Consulta cruzada
    if central_ok and dept_ok:
        cross_ok = test_cross_database_query()
    else:
        cross_ok = False
        print("\n⚠️ Saltando consulta cruzada por errores anteriores")
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS:")
    print(f"   BD Central: {'✅ OK' if central_ok else '❌ FALLO'}")
    print(f"   BD Departamento: {'✅ OK' if dept_ok else '❌ FALLO'}")
    print(f"   Consulta Cruzada: {'✅ OK' if cross_ok else '❌ FALLO'}")
    
    if central_ok and dept_ok:
        print("\n🎉 ¡Todas las conexiones funcionan correctamente!")
        print("🚀 Listo para crear los endpoints.")
    else:
        print("\n⚠️ Hay problemas de conexión que resolver.")

if __name__ == "__main__":
    main()