from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func, desc

# Importar dependencias de tu proyecto
from database import get_central_db, get_dept_db
from central_models import Paciente, DepartamentoMaster
from dept_models import Cita, Empleado, TipoCita, Departamento, EstadoCita
from schemas import CitaCreate, CitaUpdate, CitaResponse, MessageResponse

router = APIRouter()

# ===============================================
# FUNCIONES AUXILIARES
# ===============================================

def serialize_cita_complete(cita, paciente=None):
    """Serializar una cita completa con datos de ambas BD"""
    try:
        return {
            'id_cita': cita.id_cita,
            'cod_pac': cita.cod_pac,
            'paciente': {
                'nombre': f"{paciente.nom_pac} {paciente.apellido_pac}" if paciente else "No encontrado",
                'cedula': paciente.cedula if paciente else None,
                'telefono': paciente.tel_pac if paciente else None,
                'email': paciente.email_pac if paciente else None
            } if paciente else None,
            'empleado': {
                'id': cita.id_emp,
                'nombre': f"{cita.empleado.nom_emp} {cita.empleado.apellido_emp}",
                'especialidad': cita.empleado.especialidad_medica,
                'numero_licencia': cita.empleado.numero_licencia
            },
            'tipo_cita': {
                'id': cita.id_tipo_cita,
                'nombre': cita.tipo_cita.nombre_tipo,
                'duracion_default': cita.tipo_cita.duracion_default_min,
                'costo_base': float(cita.tipo_cita.costo_base) if cita.tipo_cita.costo_base else None
            },
            'departamento': {
                'id': cita.id_dept,
                'nombre': cita.departamento.nom_dept,
                'ubicacion': cita.departamento.ubicacion,
                'especialidad': cita.departamento.tipo_especialidad
            },
            'fecha_cita': cita.fecha_cita.isoformat(),
            'hora_inicio': cita.hora_inicio.strftime('%H:%M'),
            'hora_fin': cita.hora_fin.strftime('%H:%M') if cita.hora_fin else None,
            'duracion_real_min': cita.duracion_real_min,
            'motivo_consulta': cita.motivo_consulta,
            'sintomas_principales': cita.sintomas_principales,
            'diagnostico_preliminar': cita.diagnostico_preliminar,
            'diagnostico_final': cita.diagnostico_final,
            'observaciones_cita': cita.observaciones_cita,
            'recomendaciones': cita.recomendaciones,
            'requiere_seguimiento': cita.requiere_seguimiento,
            'fecha_seguimiento': cita.fecha_seguimiento.isoformat() if cita.fecha_seguimiento else None,
            'prioridad': cita.prioridad,
            'estado_cita': cita.estado_cita.value,
            'created_at': cita.created_at.isoformat() if cita.created_at else None,
            'updated_at': cita.updated_at.isoformat() if cita.updated_at else None
        }
    except Exception as e:
        print(f"Error serializando cita {cita.id_cita}: {str(e)}")
        return None

def validate_cita_data(data: CitaCreate):
    """Validar datos de entrada para citas"""
    errors = []
    
    # Validar formato de fecha
    try:
        datetime.strptime(data.fecha_cita, '%Y-%m-%d')
    except ValueError:
        errors.append("El formato de fecha debe ser YYYY-MM-DD")
    
    # Validar formato de hora
    try:
        datetime.strptime(data.hora_inicio, '%H:%M')
    except ValueError:
        errors.append("El formato de hora debe ser HH:MM")
    
    if data.hora_fin:
        try:
            datetime.strptime(data.hora_fin, '%H:%M')
        except ValueError:
            errors.append("El formato de hora_fin debe ser HH:MM")
    
    return errors

def check_schedule_conflict(
    id_emp: int, 
    fecha_cita: date, 
    hora_inicio, 
    exclude_cita_id: Optional[int] = None,
    dept_db: Session = None
):
    """Verificar conflictos de horario para un empleado"""
    query = dept_db.query(Cita).filter(
        and_(
            Cita.id_emp == id_emp,
            Cita.fecha_cita == fecha_cita,
            Cita.hora_inicio == hora_inicio,
            Cita.estado_cita.in_([EstadoCita.PROGRAMADA, EstadoCita.CONFIRMADA, EstadoCita.EN_CURSO])
        )
    )
    
    if exclude_cita_id:
        query = query.filter(Cita.id_cita != exclude_cita_id)
    
    return query.first()

# ===============================================
# ENDPOINTS DE CITAS
# ===============================================

@router.get("/")
def get_appointments(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(20, ge=1, le=100, description="Límite de registros"),
    departamento_id: Optional[int] = Query(None, description="Filtrar por departamento"),
    fecha: Optional[str] = Query(None, description="Filtrar por fecha (YYYY-MM-DD)"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    paciente_id: Optional[int] = Query(None, description="Filtrar por paciente"),
    empleado_id: Optional[int] = Query(None, description="Filtrar por empleado"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad"),
    central_db: Session = Depends(get_central_db),
    dept_db: Session = Depends(get_dept_db)
):
    """Listar todas las citas con filtros opcionales"""
    try:
        # Construir query con joins optimizados
        query = dept_db.query(Cita).options(
            joinedload(Cita.empleado).joinedload(Empleado.rol),
            joinedload(Cita.tipo_cita),
            joinedload(Cita.departamento)
        )
        
        # Aplicar filtros
        if departamento_id:
            query = query.filter(Cita.id_dept == departamento_id)
        
        if fecha:
            try:
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
                query = query.filter(Cita.fecha_cita == fecha_obj)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail='Formato de fecha inválido. Use YYYY-MM-DD'
                )
        
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                query = query.filter(Cita.fecha_cita >= fecha_desde_obj)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail='Formato de fecha_desde inválido. Use YYYY-MM-DD'
                )
        
        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                query = query.filter(Cita.fecha_cita <= fecha_hasta_obj)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail='Formato de fecha_hasta inválido. Use YYYY-MM-DD'
                )
        
        if estado:
            try:
                estado_enum = EstadoCita(estado)
                query = query.filter(Cita.estado_cita == estado_enum)
            except ValueError:
                valid_states = [e.value for e in EstadoCita]
                raise HTTPException(
                    status_code=400,
                    detail=f'Estado inválido: {estado}. Estados válidos: {valid_states}'
                )
        
        if paciente_id:
            query = query.filter(Cita.cod_pac == paciente_id)
        
        if empleado_id:
            query = query.filter(Cita.id_emp == empleado_id)
        
        if prioridad:
            query = query.filter(Cita.prioridad == prioridad)
        
        # Ordenar por fecha y hora
        query = query.order_by(desc(Cita.fecha_cita), desc(Cita.hora_inicio))
        
        # Obtener total antes de paginar
        total = query.count()
        
        # Aplicar paginación
        citas = query.offset(skip).limit(limit).all()
        
        # Obtener datos de pacientes de BD Central
        pacientes_ids = [cita.cod_pac for cita in citas]
        pacientes = central_db.query(Paciente).filter(
            Paciente.cod_pac.in_(pacientes_ids)
        ).all()
        pacientes_dict = {p.cod_pac: p for p in pacientes}
        
        # Serializar resultados
        citas_serializadas = []
        for cita in citas:
            paciente = pacientes_dict.get(cita.cod_pac)
            serialized = serialize_cita_complete(cita, paciente)
            if serialized:
                citas_serializadas.append(serialized)
        
        return {
            'success': True,
            'citas': citas_serializadas,
            'total': total,
            'skip': skip,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit,
            'has_next': skip + limit < total,
            'has_prev': skip > 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Error al obtener citas: {str(e)}'
        )

@router.post("/")
def create_appointment(
    cita_data: CitaCreate,
    central_db: Session = Depends(get_central_db),
    dept_db: Session = Depends(get_dept_db)
):
    """Crear una nueva cita"""
    try:
        # Validar datos
        errors = validate_cita_data(cita_data)
        if errors:
            raise HTTPException(status_code=400, detail={'errors': errors})
        
        # Verificar que el paciente existe en BD Central
        paciente = central_db.query(Paciente).filter(
            Paciente.cod_pac == cita_data.cod_pac
        ).first()
        if not paciente:
            raise HTTPException(
                status_code=404,
                detail='Paciente no encontrado en el sistema central'
            )
        
        # Verificar que el empleado existe en BD Departamental
        empleado = dept_db.query(Empleado).options(
            joinedload(Empleado.rol)
        ).filter(Empleado.id_emp == cita_data.id_emp).first()
        if not empleado:
            raise HTTPException(status_code=404, detail='Empleado no encontrado')
        
        # Verificar que el tipo de cita existe
        tipo_cita = dept_db.query(TipoCita).filter(
            TipoCita.id_tipo_cita == cita_data.id_tipo_cita
        ).first()
        if not tipo_cita:
            raise HTTPException(status_code=404, detail='Tipo de cita no encontrado')
        
        # Verificar que el departamento existe
        departamento = dept_db.query(Departamento).filter(
            Departamento.id_dept == cita_data.id_dept
        ).first()
        if not departamento:
            raise HTTPException(status_code=404, detail='Departamento no encontrado')
        
        # Verificar disponibilidad del empleado
        fecha_cita = datetime.strptime(cita_data.fecha_cita, '%Y-%m-%d').date()
        hora_inicio = datetime.strptime(cita_data.hora_inicio, '%H:%M').time()
        
        conflicto = check_schedule_conflict(
            cita_data.id_emp, fecha_cita, hora_inicio, None, dept_db
        )
        if conflicto:
            raise HTTPException(
                status_code=409,
                detail={
                    'error': 'El empleado ya tiene una cita programada en ese horario',
                    'cita_conflicto': {
                        'id_cita': conflicto.id_cita,
                        'paciente': conflicto.cod_pac,
                        'estado': conflicto.estado_cita.value
                    }
                }
            )
        
        # Procesar hora_fin si se proporciona
        hora_fin = None
        if cita_data.hora_fin:
            hora_fin = datetime.strptime(cita_data.hora_fin, '%H:%M').time()
        
        # Crear nueva cita
        nueva_cita = Cita(
            cod_pac=cita_data.cod_pac,
            id_emp=cita_data.id_emp,
            id_tipo_cita=cita_data.id_tipo_cita,
            id_dept=cita_data.id_dept,
            fecha_cita=fecha_cita,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            motivo_consulta=cita_data.motivo_consulta,
            sintomas_principales=cita_data.sintomas_principales,
            observaciones_cita=cita_data.observaciones_cita,
            prioridad=cita_data.prioridad,
            estado_cita=EstadoCita.PROGRAMADA,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        dept_db.add(nueva_cita)
        dept_db.commit()
        dept_db.refresh(nueva_cita)
        
        # Cargar relaciones
        nueva_cita = dept_db.query(Cita).options(
            joinedload(Cita.empleado),
            joinedload(Cita.tipo_cita),
            joinedload(Cita.departamento)
        ).filter(Cita.id_cita == nueva_cita.id_cita).first()
        
        return {
            'success': True,
            'message': 'Cita creada exitosamente',
            'data': serialize_cita_complete(nueva_cita, paciente)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        dept_db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'Error al crear cita: {str(e)}'
        )

@router.get("/today")
def get_today_appointments(
    departamento_id: Optional[int] = Query(None, description="Filtrar por departamento"),
    empleado_id: Optional[int] = Query(None, description="Filtrar por empleado"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    central_db: Session = Depends(get_central_db),
    dept_db: Session = Depends(get_dept_db)
):
    """Obtener citas del día de hoy"""
    try:
        today = date.today()
        
        # Construir query
        query = dept_db.query(Cita).options(
            joinedload(Cita.empleado).joinedload(Empleado.rol),
            joinedload(Cita.tipo_cita),
            joinedload(Cita.departamento)
        ).filter(Cita.fecha_cita == today)
        
        if departamento_id:
            query = query.filter(Cita.id_dept == departamento_id)
        
        if empleado_id:
            query = query.filter(Cita.id_emp == empleado_id)
        
        if estado:
            try:
                estado_enum = EstadoCita(estado)
                query = query.filter(Cita.estado_cita == estado_enum)
            except ValueError:
                valid_states = [e.value for e in EstadoCita]
                raise HTTPException(
                    status_code=400,
                    detail=f'Estado inválido: {estado}. Estados válidos: {valid_states}'
                )
        
        # Ordenar por hora
        citas = query.order_by(Cita.hora_inicio).all()
        
        # Obtener datos de pacientes
        pacientes_ids = [cita.cod_pac for cita in citas]
        pacientes = central_db.query(Paciente).filter(
            Paciente.cod_pac.in_(pacientes_ids)
        ).all()
        pacientes_dict = {p.cod_pac: p for p in pacientes}
        
        # Serializar resultados
        citas_serializadas = []
        for cita in citas:
            paciente = pacientes_dict.get(cita.cod_pac)
            serialized = serialize_cita_complete(cita, paciente)
            if serialized:
                citas_serializadas.append(serialized)
        
        return {
            'success': True,
            'fecha': today.isoformat(),
            'total_citas': len(citas_serializadas),
            'citas': citas_serializadas
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Error al obtener citas de hoy: {str(e)}'
        )

@router.get("/{cita_id}")
def get_appointment(
    cita_id: int,
    central_db: Session = Depends(get_central_db),
    dept_db: Session = Depends(get_dept_db)
):
    """Obtener una cita específica"""
    try:
        cita = dept_db.query(Cita).options(
            joinedload(Cita.empleado).joinedload(Empleado.rol),
            joinedload(Cita.tipo_cita),
            joinedload(Cita.departamento)
        ).filter(Cita.id_cita == cita_id).first()
        
        if not cita:
            raise HTTPException(status_code=404, detail='Cita no encontrada')
        
        # Obtener datos del paciente
        paciente = central_db.query(Paciente).filter(
            Paciente.cod_pac == cita.cod_pac
        ).first()
        
        serialized = serialize_cita_complete(cita, paciente)
        if not serialized:
            raise HTTPException(
                status_code=500,
                detail='Error al procesar datos de la cita'
            )
        
        return {
            'success': True,
            'data': serialized
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Error al obtener cita: {str(e)}'
        )

@router.put("/{cita_id}")
def update_appointment(
    cita_id: int,
    cita_data: CitaUpdate,
    dept_db: Session = Depends(get_dept_db)
):
    """Actualizar una cita existente"""
    try:
        cita = dept_db.query(Cita).filter(Cita.id_cita == cita_id).first()
        if not cita:
            raise HTTPException(status_code=404, detail='Cita no encontrada')
        
        # Actualizar campos
        update_data = cita_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                if field == 'fecha_seguimiento' and value:
                    try:
                        setattr(cita, field, datetime.strptime(value, '%Y-%m-%d').date())
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail=f'Formato de {field} inválido. Use YYYY-MM-DD'
                        )
                elif field == 'estado_cita':
                    try:
                        setattr(cita, field, EstadoCita(value))
                    except ValueError:
                        valid_states = [e.value for e in EstadoCita]
                        raise HTTPException(
                            status_code=400,
                            detail=f'Estado inválido: {value}. Estados válidos: {valid_states}'
                        )
                elif field == 'hora_fin' and value:
                    try:
                        setattr(cita, field, datetime.strptime(value, '%H:%M').time())
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail='Formato de hora_fin inválido. Use HH:MM'
                        )
                else:
                    setattr(cita, field, value)
        
        # Actualizar timestamp
        cita.updated_at = datetime.utcnow()
        
        dept_db.commit()
        dept_db.refresh(cita)
        
        return {
            'success': True,
            'message': 'Cita actualizada exitosamente',
            'data': {
                'id_cita': cita.id_cita,
                'estado_cita': cita.estado_cita.value,
                'updated_at': cita.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        dept_db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'Error al actualizar cita: {str(e)}'
        )

@router.delete("/{cita_id}")
def cancel_appointment(
    cita_id: int,
    dept_db: Session = Depends(get_dept_db)
):
    """Cancelar una cita (cambiar estado a cancelada)"""
    try:
        cita = dept_db.query(Cita).filter(Cita.id_cita == cita_id).first()
        if not cita:
            raise HTTPException(status_code=404, detail='Cita no encontrada')
        
        # Verificar que la cita se puede cancelar
        if cita.estado_cita in [EstadoCita.COMPLETADA, EstadoCita.CANCELADA]:
            raise HTTPException(
                status_code=400,
                detail=f'No se puede cancelar una cita en estado {cita.estado_cita.value}'
            )
        
        # Cambiar estado a cancelada
        cita.estado_cita = EstadoCita.CANCELADA
        cita.updated_at = datetime.utcnow()
        
        dept_db.commit()
        
        return {
            'success': True,
            'message': 'Cita cancelada exitosamente'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        dept_db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'Error al cancelar cita: {str(e)}'
        )

# ===============================================
# ENDPOINTS AUXILIARES
# ===============================================

@router.get("/types/")
def get_appointment_types(dept_db: Session = Depends(get_dept_db)):
    """Obtener tipos de citas disponibles"""
    try:
        tipos = dept_db.query(TipoCita).all()
        return {
            'success': True,
            'data': [{
                'id_tipo_cita': tipo.id_tipo_cita,
                'nombre_tipo': tipo.nombre_tipo,
                'duracion_default_min': tipo.duracion_default_min,
                'costo_base': float(tipo.costo_base) if tipo.costo_base else None,
                'descripcion_tipo': tipo.descripcion_tipo,
                'requiere_preparacion': tipo.requiere_preparacion,
                'permite_urgencia': tipo.permite_urgencia,
                'requiere_interconsulta': tipo.requiere_interconsulta
            } for tipo in tipos]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Error al obtener tipos de cita: {str(e)}'
        )

@router.get("/stats/")
def get_appointment_stats(
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    departamento_id: Optional[int] = Query(None, description="Filtrar por departamento"),
    dept_db: Session = Depends(get_dept_db)
):
    """Obtener estadísticas de citas"""
    try:
        # Fechas por defecto (último mes)
        if not fecha_desde:
            fecha_desde = (date.today() - timedelta(days=30)).isoformat()
        if not fecha_hasta:
            fecha_hasta = date.today().isoformat()
        
        fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
        
        # Query base
        query = dept_db.query(Cita).filter(
            and_(
                Cita.fecha_cita >= fecha_desde_obj,
                Cita.fecha_cita <= fecha_hasta_obj
            )
        )
        
        if departamento_id:
            query = query.filter(Cita.id_dept == departamento_id)
        
        # Obtener estadísticas
        total_citas = query.count()
        
        stats_por_estado = {}
        for estado in EstadoCita:
            count = query.filter(Cita.estado_cita == estado).count()
            stats_por_estado[estado.value] = count
        
        return {
            'success': True,
            'data': {
                'total_citas': total_citas,
                'por_estado': stats_por_estado,
                'periodo': {
                    'fecha_desde': fecha_desde,
                    'fecha_hasta': fecha_hasta
                },
                'filtros_aplicados': {
                    'departamento_id': departamento_id
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Error al obtener estadísticas: {str(e)}'
        )