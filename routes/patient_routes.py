from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_central_db
from central_models import Paciente, TipoSangre, DepartamentoMaster
from schemas import PatientCreate, PatientUpdate, PatientResponse, MessageResponse, CountResponse

router = APIRouter()


@router.get("/count", response_model=CountResponse)
def get_patients_count(
    search: Optional[str] = Query(None, description="Buscar por nombre, apellido o cédula"),
    db: Session = Depends(get_central_db)
):
    """Contar total de pacientes"""
    query = db.query(Paciente)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Paciente.nom_pac.ilike(search_filter)) |
            (Paciente.apellido_pac.ilike(search_filter)) |
            (Paciente.cedula.ilike(search_filter))
        )
    
    total = query.count()
    return {"total": total}

@router.get("/tipos-sangre")
def get_blood_types(db: Session = Depends(get_central_db)):
    """Obtener tipos de sangre disponibles"""
    tipos = db.query(TipoSangre).all()
    return [{"id": t.id_tipo_sangre, "tipo": t.tipo_sangre, "descripcion": t.descripcion} for t in tipos]

@router.get("/departamentos")
def get_departments(db: Session = Depends(get_central_db)):
    """Obtener departamentos disponibles"""
    departamentos = db.query(DepartamentoMaster).all()
    return [{"id": d.id_dept, "nombre": d.nom_dept, "especialidad": d.tipo_especialidad} for d in departamentos]

# ✅ SEGUNDO: Endpoints con paths específicos que incluyen /
@router.get("/cedula/{cedula}")
def get_patient_by_cedula(
    cedula: str,
    db: Session = Depends(get_central_db)
):
    """Buscar paciente por cédula"""
    try:
        patient = db.query(Paciente).filter(Paciente.cedula == cedula).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paciente con cédula {cedula} no encontrado"
            )
        
        return {
            "id": patient.cod_pac,
            "nombre": patient.nom_pac,
            "apellido": patient.apellido_pac,
            "cedula": patient.cedula,
            "genero": patient.genero.value if patient.genero else None,
            "estado": patient.estado_paciente.value if patient.estado_paciente else None,
            "email": patient.email_pac,
            "telefono": patient.tel_pac
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}

# ✅ TERCERO: Endpoints con parámetros variables (SIEMPRE AL FINAL)
@router.get("/{patient_id}")
def get_patient(
    patient_id: int,
    db: Session = Depends(get_central_db)
):
    """Obtener un paciente específico por ID"""
    try:
        patient = db.query(Paciente).filter(Paciente.cod_pac == patient_id).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paciente con ID {patient_id} no encontrado"
            )
        
        return {
            "id": patient.cod_pac,
            "nombre": patient.nom_pac,
            "apellido": patient.apellido_pac,
            "cedula": patient.cedula,
            "genero": patient.genero.value if patient.genero else None,
            "estado": patient.estado_paciente.value if patient.estado_paciente else None,
            "email": patient.email_pac,
            "telefono": patient.tel_pac
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}

# ✅ CUARTO: Endpoint raíz (SIEMPRE AL FINAL)
@router.get("/")
def get_patients(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Límite de registros"),
    search: Optional[str] = Query(None, description="Buscar por nombre, apellido o cédula"),
    db: Session = Depends(get_central_db)
):
    """Obtener lista de pacientes"""
    try:
        query = db.query(Paciente)
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Paciente.nom_pac.ilike(search_filter)) |
                (Paciente.apellido_pac.ilike(search_filter)) |
                (Paciente.cedula.ilike(search_filter))
            )
        
        patients = query.offset(skip).limit(limit).all()
        
        result = []
        for p in patients:
            result.append({
                "id": p.cod_pac,
                "nombre": p.nom_pac,
                "apellido": p.apellido_pac,
                "cedula": p.cedula,
                "genero": p.genero.value if p.genero else None,
                "estado": p.estado_paciente.value if p.estado_paciente else None,
                "email": p.email_pac,
                "telefono": p.tel_pac
            })
        
        return {
            "total": len(result),
            "skip": skip,
            "limit": limit,
            "data": result
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/")
def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_central_db)
):
    """Crear nuevo paciente"""
    try:
        # Verificar que no existe un paciente con la misma cédula
        existing_patient = db.query(Paciente).filter(Paciente.cedula == patient_data.cedula).first()
        if existing_patient:
            return {
                "success": False,
                "error": f"Ya existe un paciente con cédula {patient_data.cedula}"
            }
        
        # Convertir los datos
        patient_dict = patient_data.dict()
        
        # Convertir fecha de string a date si viene como string
        if patient_dict.get('fecha_nac') and isinstance(patient_dict['fecha_nac'], str):
            from datetime import datetime
            try:
                patient_dict['fecha_nac'] = datetime.strptime(patient_dict['fecha_nac'], '%Y-%m-%d').date()
            except ValueError:
                return {
                    "success": False,
                    "error": "Formato de fecha inválido. Use YYYY-MM-DD"
                }
        
        # Convertir género a enum si es necesario
        if patient_dict.get('genero'):
            from central_models import GeneroEnum
            if patient_dict['genero'] in ['M', 'F', 'OTRO']:
                patient_dict['genero'] = GeneroEnum(patient_dict['genero'])
            else:
                patient_dict['genero'] = None
        
        # Remover campos None o vacíos
        patient_dict = {k: v for k, v in patient_dict.items() if v is not None and v != ""}
        
        # Crear el paciente
        db_patient = Paciente(**patient_dict)
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        
        return {
            "success": True,
            "message": "Paciente creado exitosamente",
            "data": {
                "id": db_patient.cod_pac,
                "nombre": db_patient.nom_pac,
                "apellido": db_patient.apellido_pac,
                "cedula": db_patient.cedula,
                "genero": db_patient.genero.value if db_patient.genero else None,
                "estado": db_patient.estado_paciente.value if db_patient.estado_paciente else "ACTIVO",
                "email": db_patient.email_pac,
                "telefono": db_patient.tel_pac,
                "fecha_nac": db_patient.fecha_nac.isoformat() if db_patient.fecha_nac else None
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error al crear paciente: {str(e)}"
        }

@router.put("/{patient_id}")
def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_central_db)
):
    """Actualizar paciente existente"""
    try:
        # Buscar el paciente
        db_patient = db.query(Paciente).filter(Paciente.cod_pac == patient_id).first()
        if not db_patient:
            return {
                "success": False,
                "error": f"Paciente con ID {patient_id} no encontrado"
            }
        
        # Obtener datos a actualizar
        update_data = patient_data.dict(exclude_unset=True)
        
        # Verificar cédula única si se está actualizando
        if update_data.get('cedula') and update_data['cedula'] != db_patient.cedula:
            existing_cedula = db.query(Paciente).filter(Paciente.cedula == update_data['cedula']).first()
            if existing_cedula:
                return {
                    "success": False,
                    "error": f"Ya existe un paciente con cédula {update_data['cedula']}"
                }
        
        # Verificar email único si se está actualizando
        if update_data.get('email_pac') and update_data['email_pac'] != db_patient.email_pac:
            existing_email = db.query(Paciente).filter(Paciente.email_pac == update_data['email_pac']).first()
            if existing_email:
                return {
                    "success": False,
                    "error": f"Ya existe un paciente con email {update_data['email_pac']}"
                }
        
        # Actualizar campos
        for field, value in update_data.items():
            if value is not None and value != "":
                # Convertir fecha si viene como string
                if field == 'fecha_nac' and isinstance(value, str):
                    from datetime import datetime
                    try:
                        value = datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError:
                        return {
                            "success": False,
                            "error": "Formato de fecha inválido. Use YYYY-MM-DD"
                        }
                
                # Convertir enums
                elif field == 'genero' and isinstance(value, str):
                    from central_models import GeneroEnum
                    if value in ['M', 'F', 'OTRO']:
                        value = GeneroEnum(value)
                    else:
                        continue  # Saltar valores inválidos
                        
                elif field == 'estado_paciente' and isinstance(value, str):
                    from central_models import EstadoPaciente
                    if value in ['ACTIVO', 'INACTIVO', 'FALLECIDO', 'TRANSFERIDO']:
                        value = EstadoPaciente(value)
                    else:
                        continue  # Saltar valores inválidos
                
                setattr(db_patient, field, value)
        
        db.commit()
        db.refresh(db_patient)
        
        return {
            "success": True,
            "message": "Paciente actualizado exitosamente",
            "data": {
                "id": db_patient.cod_pac,
                "nombre": db_patient.nom_pac,  # ✅ CORREGIDO: era nom_emp
                "apellido": db_patient.apellido_pac,
                "cedula": db_patient.cedula,
                "genero": db_patient.genero.value if db_patient.genero else None,
                "estado": db_patient.estado_paciente.value if db_patient.estado_paciente else None,
                "email": db_patient.email_pac,
                "telefono": db_patient.tel_pac,
                "fecha_nac": db_patient.fecha_nac.isoformat() if db_patient.fecha_nac else None
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error al actualizar paciente: {str(e)}"
        }
    

@router.delete("/{patient_id}")
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_central_db)
):
    """Eliminar paciente (cambiar estado a INACTIVO)"""
    try:
        db_patient = db.query(Paciente).filter(Paciente.cod_pac == patient_id).first()
        if not db_patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paciente con ID {patient_id} no encontrado"
            )
        
        # En lugar de eliminar, cambiar estado a INACTIVO
        from central_models import EstadoPaciente
        db_patient.estado_paciente = EstadoPaciente.INACTIVO
        db.commit()
        
        return {
            "success": True,
            "message": f"Paciente {patient_id} marcado como inactivo",
            "data": {
                "id": db_patient.cod_pac,
                "nombre": db_patient.nom_pac,
                "apellido": db_patient.apellido_pac,
                "estado_anterior": "ACTIVO",
                "estado_actual": "INACTIVO"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar paciente: {str(e)}"
        )