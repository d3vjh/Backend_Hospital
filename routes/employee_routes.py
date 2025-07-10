from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_dept_db
from dept_models import Empleado, RolEmpleado, Departamento
from schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse, MessageResponse, CountResponse

router = APIRouter()

# ✅ PRIMERO: Endpoints específicos
@router.get("/raw")
def get_raw_data():
   """Endpoint sin BD para probar que el router funciona"""
   return {
       "message": "Router de empleados funcionando",
       "endpoints": [
           "/employees/raw",
           "/employees/simple", 
           "/employees/debug",
           "/employees/count",
           "/employees/roles",
           "/employees/departamentos"
       ]
   }

@router.post("/debug")
def debug_create_employee(request_data: dict):
   """Ver exactamente qué datos llegan"""
   return {
       "received_data": request_data,
       "data_types": {k: str(type(v)) for k, v in request_data.items()},
       "message": "Datos recibidos correctamente para debug"
   }

@router.get("/simple")
def get_employees_simple(db: Session = Depends(get_dept_db)):
   """Endpoint simple para probar conexión"""
   try:
       employees = db.query(Empleado).limit(5).all()
       
       result = []
       for e in employees:
           result.append({
               "id": e.id_emp,
               "nombre": e.nom_emp,
               "apellido": e.apellido_emp,
               "cedula": e.cedula,
               "especialidad": e.especialidad_medica,
               "estado": e.estado_empleado.value if e.estado_empleado else None,
               "email": e.email_emp,
               "telefono": e.tel_emp
           })
       
       return {
           "success": True,
           "count": len(result),
           "data": result
       }
   except Exception as e:
       return {
           "success": False,
           "error": str(e)
       }

@router.get("/count")
def get_employees_count(
   search: Optional[str] = Query(None, description="Buscar por nombre, apellido o cédula"),
   db: Session = Depends(get_dept_db)
):
   """Contar total de empleados"""
   try:
       query = db.query(Empleado)
       
       if search:
           search_filter = f"%{search}%"
           query = query.filter(
               (Empleado.nom_emp.ilike(search_filter)) |
               (Empleado.apellido_emp.ilike(search_filter)) |
               (Empleado.cedula.ilike(search_filter)) |
               (Empleado.especialidad_medica.ilike(search_filter))
           )
       
       total = query.count()
       return {"total": total}
   except Exception as e:
       return {"error": str(e)}

@router.get("/roles")
def get_employee_roles(db: Session = Depends(get_dept_db)):
   """Obtener roles de empleados disponibles"""
   try:
       roles = db.query(RolEmpleado).all()
       return [
           {
               "id": r.id_rol, 
               "nombre": r.nombre_rol, 
               "descripcion": r.descripcion_rol,
               "nivel_acceso": r.nivel_acceso,
               "puede_prescribir": r.puede_prescribir,
               "puede_ver_historias": r.puede_ver_historias
           } 
           for r in roles
       ]
   except Exception as e:
       return {"error": str(e)}

@router.get("/departamentos")
def get_departments(db: Session = Depends(get_dept_db)):
   """Obtener departamentos disponibles"""
   try:
       departamentos = db.query(Departamento).all()
       return [
           {
               "id": d.id_dept, 
               "nombre": d.nom_dept, 
               "especialidad": d.tipo_especialidad,
               "ubicacion": d.ubicacion
           } 
           for d in departamentos
       ]
   except Exception as e:
       return {"error": str(e)}

@router.get("/test-data")
def get_test_data():
   """Datos de ejemplo para probar el POST"""
   return {
       "ejemplo_empleado": {
           "nom_emp": "Dr. Carlos",
           "apellido_emp": "Test Médico",
           "cedula": "987654321",
           "email_emp": "carlos.test@hospital.com",
           "tel_emp": "300-987-6543",
           "fecha_nacimiento": "1985-03-20",
           "especialidad_medica": "Cardiología Intervencionista",
           "numero_licencia": "LIC123456",
           "universidad_titulo": "Universidad Nacional",
           "ano_graduacion": 2010,
           "id_dept": 1,
           "id_rol": 2
       },
       "roles_disponibles": "Ver /employees/roles",
       "departamentos_disponibles": "Ver /employees/departamentos"
   }

# ✅ SEGUNDO: Endpoints con paths específicos
@router.get("/cedula/{cedula}")
def get_employee_by_cedula(
   cedula: str,
   db: Session = Depends(get_dept_db)
):
   """Buscar empleado por cédula"""
   try:
       employee = db.query(Empleado).filter(Empleado.cedula == cedula).first()
       
       if not employee:
           return {
               "success": False,
               "error": f"Empleado con cédula {cedula} no encontrado"
           }
       
       return {
           "success": True,
           "data": {
               "id": employee.id_emp,
               "nombre": employee.nom_emp,
               "apellido": employee.apellido_emp,
               "cedula": employee.cedula,
               "especialidad": employee.especialidad_medica,
               "estado": employee.estado_empleado.value if employee.estado_empleado else None,
               "email": employee.email_emp,
               "telefono": employee.tel_emp,
               "licencia": employee.numero_licencia
           }
       }
   except Exception as e:
       return {"success": False, "error": str(e)}

@router.get("/especialidad/{especialidad}")
def get_employees_by_specialty(
   especialidad: str,
   db: Session = Depends(get_dept_db)
):
   """Buscar empleados por especialidad"""
   try:
       employees = db.query(Empleado).filter(
           Empleado.especialidad_medica.ilike(f"%{especialidad}%")
       ).all()
       
       result = []
       for e in employees:
           result.append({
               "id": e.id_emp,
               "nombre": e.nom_emp,
               "apellido": e.apellido_emp,
               "especialidad": e.especialidad_medica,
               "licencia": e.numero_licencia,
               "estado": e.estado_empleado.value if e.estado_empleado else None
           })
       
       return {
           "success": True,
           "count": len(result),
           "especialidad_buscada": especialidad,
           "data": result
       }
   except Exception as e:
       return {"success": False, "error": str(e)}

# ✅ TERCERO: Endpoints con parámetros variables
@router.get("/{employee_id}")
def get_employee(
   employee_id: int,
   db: Session = Depends(get_dept_db)
):
   """Obtener un empleado específico por ID"""
   try:
       employee = db.query(Empleado).filter(Empleado.id_emp == employee_id).first()
       
       if not employee:
           return {
               "success": False,
               "error": f"Empleado con ID {employee_id} no encontrado"
           }
       
       return {
           "success": True,
           "data": {
               "id": employee.id_emp,
               "nombre": employee.nom_emp,
               "apellido": employee.apellido_emp,
               "cedula": employee.cedula,
               "especialidad": employee.especialidad_medica,
               "estado": employee.estado_empleado.value if employee.estado_empleado else None,
               "email": employee.email_emp,
               "telefono": employee.tel_emp,
               "licencia": employee.numero_licencia,
               "universidad": employee.universidad_titulo,
               "ano_graduacion": employee.ano_graduacion,
               "turno": employee.turno_preferido,
               "fecha_contratacion": employee.fecha_contratacion.isoformat() if employee.fecha_contratacion else None
           }
       }
   except Exception as e:
       return {"success": False, "error": str(e)}

# ✅ CUARTO: Endpoint raíz
@router.get("/")
def get_employees(
   skip: int = Query(0, ge=0, description="Registros a saltar"),
   limit: int = Query(10, ge=1, le=100, description="Límite de registros"),
   search: Optional[str] = Query(None, description="Buscar por nombre, apellido, cédula o especialidad"),
   estado: Optional[str] = Query(None, description="Filtrar por estado"),
   db: Session = Depends(get_dept_db)
):
   """Obtener lista de empleados"""
   try:
       query = db.query(Empleado)
       
       # Filtro de búsqueda
       if search:
           search_filter = f"%{search}%"
           query = query.filter(
               (Empleado.nom_emp.ilike(search_filter)) |
               (Empleado.apellido_emp.ilike(search_filter)) |
               (Empleado.cedula.ilike(search_filter)) |
               (Empleado.especialidad_medica.ilike(search_filter))
           )
       
       # Filtro por estado
       if estado:
           from dept_models import EstadoEmpleado
           if estado.upper() in ['ACTIVO', 'INACTIVO', 'VACACIONES', 'LICENCIA']:
               query = query.filter(Empleado.estado_empleado == EstadoEmpleado(estado.upper()))
       
       employees = query.offset(skip).limit(limit).all()
       
       result = []
       for e in employees:
           result.append({
               "id": e.id_emp,
               "nombre": e.nom_emp,
               "apellido": e.apellido_emp,
               "cedula": e.cedula,
               "especialidad": e.especialidad_medica,
               "estado": e.estado_empleado.value if e.estado_empleado else None,
               "email": e.email_emp,
               "telefono": e.tel_emp,
               "licencia": e.numero_licencia,
               "turno": e.turno_preferido
           })
       
       return {
           "success": True,
           "total": len(result),
           "skip": skip,
           "limit": limit,
           "data": result
       }
   except Exception as e:
       return {"success": False, "error": str(e)}

# ✅ ENDPOINTS DE ESCRITURA
@router.post("/")
def create_employee(
   employee_data: dict,
   db: Session = Depends(get_dept_db)
):
   """Crear nuevo empleado"""
   try:
       # Validar campos requeridos manualmente
       required_fields = ['nom_emp', 'apellido_emp', 'cedula', 'fecha_nacimiento', 'id_dept', 'id_rol']
       for field in required_fields:
           if field not in employee_data or not employee_data[field]:
               return {
                   "success": False,
                   "error": f"Campo requerido faltante: {field}"
               }
       
       # Verificar que no existe un empleado con la misma cédula
       existing_employee = db.query(Empleado).filter(Empleado.cedula == employee_data['cedula']).first()
       if existing_employee:
           return {
               "success": False,
               "error": f"Ya existe un empleado con cédula {employee_data['cedula']}"
           }
       
       # Verificar email único si se proporciona
       if employee_data.get('email_emp'):
           existing_email = db.query(Empleado).filter(Empleado.email_emp == employee_data['email_emp']).first()
           if existing_email:
               return {
                   "success": False,
                   "error": f"Ya existe un empleado con email {employee_data['email_emp']}"
               }
       
       # Verificar que el departamento existe
       departamento = db.query(Departamento).filter(Departamento.id_dept == employee_data['id_dept']).first()
       if not departamento:
           return {
               "success": False,
               "error": f"Departamento con ID {employee_data['id_dept']} no existe"
           }
       
       # Verificar que el rol existe
       rol = db.query(RolEmpleado).filter(RolEmpleado.id_rol == employee_data['id_rol']).first()
       if not rol:
           return {
               "success": False,
               "error": f"Rol con ID {employee_data['id_rol']} no existe"
           }
       
       # Convertir fechas de string a date
       if employee_data.get('fecha_nacimiento') and isinstance(employee_data['fecha_nacimiento'], str):
           from datetime import datetime
           try:
               employee_data['fecha_nacimiento'] = datetime.strptime(employee_data['fecha_nacimiento'], '%Y-%m-%d').date()
           except ValueError:
               return {
                   "success": False,
                   "error": "Formato de fecha de nacimiento inválido. Use YYYY-MM-DD"
               }
       
       if employee_data.get('fecha_contratacion') and isinstance(employee_data['fecha_contratacion'], str):
           from datetime import datetime
           try:
               employee_data['fecha_contratacion'] = datetime.strptime(employee_data['fecha_contratacion'], '%Y-%m-%d').date()
           except ValueError:
               return {
                   "success": False,
                   "error": "Formato de fecha de contratación inválido. Use YYYY-MM-DD"
               }
       elif not employee_data.get('fecha_contratacion'):
           from datetime import date
           employee_data['fecha_contratacion'] = date.today()
       
       # Remover campos None o vacíos
       employee_dict = {k: v for k, v in employee_data.items() if v is not None and v != ""}
       
       # Crear el empleado
       db_employee = Empleado(**employee_dict)
       db.add(db_employee)
       db.commit()
       db.refresh(db_employee)
       
       return {
           "success": True,
           "message": "Empleado creado exitosamente",
           "data": {
               "id": db_employee.id_emp,
               "nombre": db_employee.nom_emp,
               "apellido": db_employee.apellido_emp,
               "cedula": db_employee.cedula,
               "especialidad": db_employee.especialidad_medica,
               "estado": db_employee.estado_empleado.value if db_employee.estado_empleado else "ACTIVO",
               "email": db_employee.email_emp,
               "telefono": db_employee.tel_emp,
               "licencia": db_employee.numero_licencia,
               "departamento": departamento.nom_dept,
               "rol": rol.nombre_rol,
               "fecha_contratacion": db_employee.fecha_contratacion.isoformat() if db_employee.fecha_contratacion else None
           }
       }
       
   except Exception as e:
       return {
           "success": False,
           "error": f"Error al crear empleado: {str(e)}"
       }

@router.put("/{employee_id}")
def update_employee(
   employee_id: int,
   employee_data: dict,
   db: Session = Depends(get_dept_db)
):
   """Actualizar empleado existente"""
   try:
       # Buscar el empleado
       db_employee = db.query(Empleado).filter(Empleado.id_emp == employee_id).first()
       if not db_employee:
           return {
               "success": False,
               "error": f"Empleado con ID {employee_id} no encontrado"
           }
       
       # Verificar cédula única si se está actualizando
       if employee_data.get('cedula') and employee_data['cedula'] != db_employee.cedula:
           existing_cedula = db.query(Empleado).filter(Empleado.cedula == employee_data['cedula']).first()
           if existing_cedula:
               return {
                   "success": False,
                   "error": f"Ya existe un empleado con cédula {employee_data['cedula']}"
               }
       
       # Actualizar campos
       for field, value in employee_data.items():
           if value is not None and value != "":
               # Convertir fechas si vienen como string
               if field in ['fecha_nacimiento', 'fecha_contratacion'] and isinstance(value, str):
                   from datetime import datetime
                   try:
                       value = datetime.strptime(value, '%Y-%m-%d').date()
                   except ValueError:
                       return {
                           "success": False,
                           "error": f"Formato de {field} inválido. Use YYYY-MM-DD"
                       }
               
               # Convertir estado si viene como string
               elif field == 'estado_empleado' and isinstance(value, str):
                   from dept_models import EstadoEmpleado
                   if value.upper() in ['ACTIVO', 'INACTIVO', 'VACACIONES', 'LICENCIA']:
                       value = EstadoEmpleado(value.upper())
                   else:
                       continue
               
               setattr(db_employee, field, value)
       
       db.commit()
       db.refresh(db_employee)
       
       return {
           "success": True,
           "message": "Empleado actualizado exitosamente",
           "data": {
               "id": db_employee.id_emp,
               "nombre": db_employee.nom_emp,
               "apellido": db_employee.apellido_emp,
               "cedula": db_employee.cedula,
               "especialidad": db_employee.especialidad_medica,
               "estado": db_employee.estado_empleado.value if db_employee.estado_empleado else None,
               "email": db_employee.email_emp,
               "telefono": db_employee.tel_emp,
               "licencia": db_employee.numero_licencia,
               "turno": db_employee.turno_preferido
           }
       }
       
   except Exception as e:
       return {
           "success": False,
           "error": f"Error al actualizar empleado: {str(e)}"
       }

@router.delete("/{employee_id}")
def delete_employee(
   employee_id: int,
   db: Session = Depends(get_dept_db)
):
   """Eliminar empleado (cambiar estado a INACTIVO)"""
   try:
       db_employee = db.query(Empleado).filter(Empleado.id_emp == employee_id).first()
       if not db_employee:
           return {
               "success": False,
               "error": f"Empleado con ID {employee_id} no encontrado"
           }
       
       # En lugar de eliminar, cambiar estado a INACTIVO
       from dept_models import EstadoEmpleado
       estado_anterior = db_employee.estado_empleado.value if db_employee.estado_empleado else "ACTIVO"
       db_employee.estado_empleado = EstadoEmpleado.INACTIVO
       db.commit()
       
       return {
           "success": True,
           "message": f"Empleado {employee_id} marcado como inactivo",
           "data": {
               "id": db_employee.id_emp,
               "nombre": db_employee.nom_emp,
               "apellido": db_employee.apellido_emp,
               "especialidad": db_employee.especialidad_medica,
               "estado_anterior": estado_anterior,
               "estado_actual": "INACTIVO"
           }
       }
       
   except Exception as e:
       return {
           "success": False,
           "error": f"Error al eliminar empleado: {str(e)}"
       }