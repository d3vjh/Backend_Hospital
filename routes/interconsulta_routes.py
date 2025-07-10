from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import datetime, date

from database import get_central_db, get_dept_db
from central_models import Paciente
from dept_models import Interconsulta, Empleado
from schemas import InterconsultaCreate, InterconsultaResponse, MessageResponse
from sqlalchemy import and_
from datetime import timedelta

router = APIRouter()

# ===============================================
# ENDPOINTS DE INTERCONSULTAS
# ===============================================

@router.get("/")
def get_interconsultas(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    urgente: Optional[bool] = Query(None, description="Filtrar por urgencia"),
    empleado_id: Optional[int] = Query(None, description="Filtrar por empleado"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    central_db: Session = Depends(get_central_db),
    dept_db: Session = Depends(get_dept_db)
):
    """Listar interconsultas con filtros"""
    try:
        query = dept_db.query(Interconsulta).options(
            joinedload(Interconsulta.empleado_solicitante),
            joinedload(Interconsulta.cita_origen)
        )
        
        if estado:
            query = query.filter(Interconsulta.estado_interconsulta == estado)
        
        if urgente is not None:
            query = query.filter(Interconsulta.urgente == urgente)
        
        if empleado_id:
            query = query.filter(Interconsulta.id_emp_solicitante == empleado_id)
        
        if fecha_desde:
            try:
                fecha_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                query = query.filter(Interconsulta.fecha_solicitud >= fecha_obj)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail='Formato de fecha inválido. Use YYYY-MM-DD'
                )
        
        # Obtener total y aplicar paginación
        total = query.count()
        interconsultas = query.order_by(
            Interconsulta.urgente.desc(), 
            Interconsulta.fecha_solicitud.desc()
        ).offset(skip).limit(limit).all()
        
        # Obtener datos de pacientes
        pacientes_ids = [ic.cod_pac for ic in interconsultas]
        pacientes = central_db.query(Paciente).filter(
            Paciente.cod_pac.in_(pacientes_ids)
        ).all()
        pacientes_dict = {p.cod_pac: p for p in pacientes}
        
        # Serializar con datos del paciente
        result = []
        for ic in interconsultas:
            paciente = pacientes_dict.get(ic.cod_pac)
            
            result.append({
                'id_interconsulta': ic.id_interconsulta,
                'cod_pac': ic.cod_pac,
                'paciente': {
                    'nombre': f"{paciente.nom_pac} {paciente.apellido_pac}" if paciente else "No encontrado",
                    'cedula': paciente.cedula if paciente else None
                } if paciente else None,
                'medico_solicitante': {
                    'id': ic.id_emp_solicitante,
                    'nombre': f"{ic.empleado_solicitante.nom_emp} {ic.empleado_solicitante.apellido_emp}",
                    'especialidad': ic.empleado_solicitante.especialidad_medica
                },
                'dept_destino': ic.dept_destino_nombre,
                'motivo': ic.motivo_interconsulta,
                'hallazgos_relevantes': ic.hallazgos_relevantes,
                'pregunta_especifica': ic.pregunta_especifica,
                'urgente': ic.urgente,
                'fecha_solicitud': ic.fecha_solicitud.isoformat(),
                'fecha_respuesta_esperada': ic.fecha_respuesta_esperada.isoformat() if ic.fecha_respuesta_esperada else None,
                'estado': ic.estado_interconsulta,
                'respuesta': ic.respuesta_interconsulta,
                'respondente': ic.nombre_respondente,
                'fecha_respuesta': ic.fecha_respuesta_recibida.isoformat() if ic.fecha_respuesta_recibida else None
            })
        
        return {
            'success': True,
            'interconsultas': result,
            'total': total,
            'skip': skip,
            'limit': limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Error al obtener interconsultas: {str(e)}'
        )

@router.post("/")
def create_interconsulta(
    interconsulta_data: InterconsultaCreate,
    central_db: Session = Depends(get_central_db),
    dept_db: Session = Depends(get_dept_db)
):
    """Crear nueva interconsulta"""
    try:
        # Verificar paciente existe
        paciente = central_db.query(Paciente).filter(
            Paciente.cod_pac == interconsulta_data.cod_pac
        ).first()
        if not paciente:
            raise HTTPException(status_code=404, detail='Paciente no encontrado')
        
        # Verificar empleado existe
        empleado = dept_db.query(Empleado).filter(
            Empleado.id_emp == interconsulta_data.id_emp_solicitante
        ).first()
        if not empleado:
            raise HTTPException(status_code=404, detail='Empleado no encontrado')
        
        # Crear interconsulta
        nueva_interconsulta = Interconsulta(
            cod_pac=interconsulta_data.cod_pac,
            id_cita_origen=interconsulta_data.id_cita_origen,
            id_emp_solicitante=interconsulta_data.id_emp_solicitante,
            id_dept_solicitante=empleado.id_dept,
            dept_destino_nombre=interconsulta_data.dept_destino_nombre,
            motivo_interconsulta=interconsulta_data.motivo_interconsulta,
            hallazgos_relevantes=interconsulta_data.hallazgos_relevantes,
            pregunta_especifica=interconsulta_data.pregunta_especifica,
            urgente=interconsulta_data.urgente,
            fecha_respuesta_esperada=datetime.strptime(
                interconsulta_data.fecha_respuesta_esperada, '%Y-%m-%d'
            ).date() if interconsulta_data.fecha_respuesta_esperada else None,
            estado_interconsulta='PENDIENTE',
            fecha_solicitud=date.today(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        dept_db.add(nueva_interconsulta)
        dept_db.commit()
        dept_db.refresh(nueva_interconsulta)
        
        return {
            'success': True,
            'message': 'Interconsulta creada exitosamente',
            'data': {
                'id_interconsulta': nueva_interconsulta.id_interconsulta,
                'estado': nueva_interconsulta.estado_interconsulta,
                'fecha_solicitud': nueva_interconsulta.fecha_solicitud.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        dept_db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'Error al crear interconsulta: {str(e)}'
        )

@router.put("/{interconsulta_id}/responder")
def responder_interconsulta(
    interconsulta_id: int,
    respuesta_data: dict,
    dept_db: Session = Depends(get_dept_db)
):
    """Responder una interconsulta"""
    try:
        interconsulta = dept_db.query(Interconsulta).filter(
            Interconsulta.id_interconsulta == interconsulta_id
        ).first()
        
        if not interconsulta:
            raise HTTPException(status_code=404, detail='Interconsulta no encontrada')
        
        # Actualizar respuesta
        interconsulta.respuesta_interconsulta = respuesta_data.get('respuesta_interconsulta')
        interconsulta.nombre_respondente = respuesta_data.get('nombre_respondente')
        interconsulta.fecha_respuesta_recibida = date.today()
        interconsulta.estado_interconsulta = 'RESPONDIDA'
        interconsulta.updated_at = datetime.utcnow()
        
        dept_db.commit()
        
        return {
            'success': True,
            'message': 'Interconsulta respondida exitosamente'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        dept_db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'Error al responder interconsulta: {str(e)}'
        )

@router.get("/{interconsulta_id}")
def get_interconsulta(
    interconsulta_id: int,
    central_db: Session = Depends(get_central_db),
    dept_db: Session = Depends(get_dept_db)
):
    """Obtener una interconsulta específica"""
    try:
        interconsulta = dept_db.query(Interconsulta).options(
            joinedload(Interconsulta.empleado_solicitante),
            joinedload(Interconsulta.cita_origen)
        ).filter(Interconsulta.id_interconsulta == interconsulta_id).first()
        
        if not interconsulta:
            raise HTTPException(status_code=404, detail='Interconsulta no encontrada')
        
        # Obtener datos del paciente
        paciente = central_db.query(Paciente).filter(
            Paciente.cod_pac == interconsulta.cod_pac
        ).first()
        
        result = {
            'id_interconsulta': interconsulta.id_interconsulta,
            'cod_pac': interconsulta.cod_pac,
            'paciente': {
                'nombre': f"{paciente.nom_pac} {paciente.apellido_pac}" if paciente else "No encontrado",
                'cedula': paciente.cedula if paciente else None,
                'telefono': paciente.tel_pac if paciente else None
            } if paciente else None,
            'medico_solicitante': {
                'nombre': f"{interconsulta.empleado_solicitante.nom_emp} {interconsulta.empleado_solicitante.apellido_emp}",
                'especialidad': interconsulta.empleado_solicitante.especialidad_medica
            },
            'cita_origen': {
                'id': interconsulta.id_cita_origen,
                'fecha': interconsulta.cita_origen.fecha_cita.isoformat() if interconsulta.cita_origen else None
            } if interconsulta.cita_origen else None,
            'dept_destino': interconsulta.dept_destino_nombre,
            'motivo': interconsulta.motivo_interconsulta,
            'hallazgos_relevantes': interconsulta.hallazgos_relevantes,
            'pregunta_especifica': interconsulta.pregunta_especifica,
            'urgente': interconsulta.urgente,
            'fecha_solicitud': interconsulta.fecha_solicitud.isoformat(),
            'fecha_respuesta_esperada': interconsulta.fecha_respuesta_esperada.isoformat() if interconsulta.fecha_respuesta_esperada else None,
            'estado': interconsulta.estado_interconsulta,
            'respuesta': interconsulta.respuesta_interconsulta,
            'respondente': interconsulta.nombre_respondente,
            'fecha_respuesta': interconsulta.fecha_respuesta_recibida.isoformat() if interconsulta.fecha_respuesta_recibida else None
        }
        
        return {
            'success': True,
            'data': result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Error al obtener interconsulta: {str(e)}'
        )

@router.get("/stats/")
def get_interconsultas_stats(
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    dept_db: Session = Depends(get_dept_db)
):
    """Estadísticas de interconsultas"""
    try:
        if not fecha_desde:
            fecha_desde = (date.today() - timedelta(days=30)).isoformat()
        if not fecha_hasta:
            fecha_hasta = date.today().isoformat()
        
        fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
        
        query = dept_db.query(Interconsulta).filter(
            and_(
                Interconsulta.fecha_solicitud >= fecha_desde_obj,
                Interconsulta.fecha_solicitud <= fecha_hasta_obj
            )
        )
        
        total = query.count()
        urgentes = query.filter(Interconsulta.urgente == True).count()
        pendientes = query.filter(Interconsulta.estado_interconsulta == 'PENDIENTE').count()
        respondidas = query.filter(Interconsulta.estado_interconsulta == 'RESPONDIDA').count()
        
        return {
            'success': True,
            'data': {
                'total_interconsultas': total,
                'urgentes': urgentes,
                'pendientes': pendientes,
                'respondidas': respondidas,
                'periodo': {
                    'desde': fecha_desde,
                    'hasta': fecha_hasta
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Error al obtener estadísticas: {str(e)}'
        )