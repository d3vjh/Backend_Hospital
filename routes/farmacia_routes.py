from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import datetime, date

from database import get_central_db, get_dept_db
from sqlalchemy import and_, or_, func
from central_models import Paciente, HistoriaClinica, Medicamento, Laboratorio, CategoriaMedicamento
from dept_models import SolicitudPrescripcion, DetalleSolicitudMedicamento, Empleado
from schemas import SolicitudPrescripcionCreate, SolicitudPrescripcionResponse, MessageResponse

router = APIRouter()

# ===============================================
# ENDPOINTS DE FARMACIA
# ===============================================

@router.get("/medicamentos/buscar")
def buscar_medicamentos(
    nombre: Optional[str] = Query(None, description="Buscar por nombre"),
    principio_activo: Optional[str] = Query(None, description="Buscar por principio activo"),
    categoria: Optional[str] = Query(None, description="Buscar por categoría"),
    solo_disponibles: bool = Query(True, description="Solo medicamentos disponibles"),
    limit: int = Query(50, ge=1, le=100),
    central_db: Session = Depends(get_central_db)
):
    """Buscar medicamentos disponibles en farmacia central"""
    try:
        query = central_db.query(Medicamento).options(
            joinedload(Medicamento.laboratorio),
            joinedload(Medicamento.categoria)
        )
        
        if nombre:
            query = query.filter(Medicamento.nom_med.ilike(f'%{nombre}%'))
        
        if principio_activo:
            query = query.filter(Medicamento.principio_activo.ilike(f'%{principio_activo}%'))
        
        if categoria:
            query = query.join(CategoriaMedicamento).filter(
                CategoriaMedicamento.nombre_categoria.ilike(f'%{categoria}%')
            )
        
        if solo_disponibles:
            from central_models import EstadoMedicamento
            query = query.filter(
                and_(
                    Medicamento.estado_medicamento == EstadoMedicamento.DISPONIBLE,
                    Medicamento.stock_actual > 0
                )
            )
        
        medicamentos = query.limit(limit).all()
        
        result = [{
            'cod_med': med.cod_med,
            'nom_med': med.nom_med,
            'principio_activo': med.principio_activo,
            'concentracion': med.concentracion,
            'forma_farmaceutica': med.forma_farmaceutica,
            'stock_actual': med.stock_actual,
            'stock_minimo': med.stock_minimo,
            'precio_unitario': float(med.precio_unitario) if med.precio_unitario else None,
            'laboratorio': {
                'id': med.laboratorio.id_laboratorio,
                'nombre': med.laboratorio.nombre_laboratorio
            } if med.laboratorio else None,
            'categoria': {
                'id': med.categoria.id_categoria,
                'nombre': med.categoria.nombre_categoria
            } if med.categoria else None,
            'fecha_vencimiento': med.fecha_vencimiento.isoformat() if med.fecha_vencimiento else None,
            'estado': med.estado_medicamento.value,
            'dias_hasta_vencimiento': (med.fecha_vencimiento - date.today()).days if med.fecha_vencimiento else None
        } for med in medicamentos]
        
        return {
            'success': True,
            'medicamentos': result,
            'total': len(result),
            'filtros': {
                'nombre': nombre,
                'principio_activo': principio_activo,
                'categoria': categoria,
                'solo_disponibles': solo_disponibles
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Error al buscar medicamentos: {str(e)}'
        )

@router.get("/solicitudes-prescripcion")
def get_solicitudes_prescripcion(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    urgente: Optional[bool] = Query(None, description="Filtrar por urgencia"),
    empleado_id: Optional[int] = Query(None, description="Filtrar por empleado"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    central_db: Session = Depends(get_central_db),
    dept_db: Session = Depends(get_dept_db)
):
    """Listar solicitudes de prescripción a farmacia"""
    try:
        query = dept_db.query(SolicitudPrescripcion).options(
            joinedload(SolicitudPrescripcion.empleado_prescriptor),
            joinedload(SolicitudPrescripcion.cita)
        )
        
        if estado:
            query = query.filter(SolicitudPrescripcion.estado_solicitud == estado)
        
        if urgente is not None:
            query = query.filter(SolicitudPrescripcion.urgente == urgente)
        
        if empleado_id:
            query = query.filter(SolicitudPrescripcion.id_emp_prescriptor == empleado_id)
        
        if fecha_desde:
            try:
                fecha_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                query = query.filter(
                    func.date(SolicitudPrescripcion.fecha_solicitud) >= fecha_obj
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail='Formato de fecha inválido. Use YYYY-MM-DD'
                )
        
        # Obtener total y aplicar paginación
        total = query.count()
        solicitudes = query.order_by(
            SolicitudPrescripcion.urgente.desc(),
            SolicitudPrescripcion.fecha_solicitud.desc()
        ).offset(skip).limit(limit).all()
        
        # Obtener datos de pacientes de BD Central
        pacientes_ids = [sol.cod_pac for sol in solicitudes]
        pacientes = central_db.query(Paciente).filter(
            Paciente.cod_pac.in_(pacientes_ids)
        ).all()
        pacientes_dict = {p.cod_pac: p for p in pacientes}
        
        result = []
        for sol in solicitudes:
            paciente = pacientes_dict.get(sol.cod_pac)
            
            # Obtener medicamentos solicitados
            medicamentos = dept_db.query(DetalleSolicitudMedicamento).filter(
                DetalleSolicitudMedicamento.id_solicitud == sol.id_solicitud
            ).all()
            
            result.append({
                'id_solicitud': sol.id_solicitud,
                'cod_pac': sol.cod_pac,
                'paciente': {
                    'nombre': f"{paciente.nom_pac} {paciente.apellido_pac}" if paciente else "No encontrado",
                    'cedula': paciente.cedula if paciente else None,
                    'telefono': paciente.tel_pac if paciente else None
                } if paciente else None,
                'medico': {
                    'id': sol.id_emp_prescriptor,
                    'nombre': f"{sol.empleado_prescriptor.nom_emp} {sol.empleado_prescriptor.apellido_emp}",
                    'especialidad': sol.empleado_prescriptor.especialidad_medica,
                    'numero_licencia': sol.empleado_prescriptor.numero_licencia
                },
                'cita': {
                    'id': sol.id_cita,
                    'fecha': sol.cita.fecha_cita.isoformat() if sol.cita else None
                } if sol.cita else None,
                'diagnostico': sol.diagnostico,
                'observaciones_medicas': sol.observaciones_medicas,
                'urgente': sol.urgente,
                'fecha_solicitud': sol.fecha_solicitud.isoformat(),
                'estado': sol.estado_solicitud,
                'total_medicamentos': len(medicamentos),
                'medicamentos': [{
                    'nombre': med.nombre_medicamento,
                    'principio_activo': med.principio_activo,
                    'concentracion': med.concentracion,
                    'dosis': med.dosis,
                    'frecuencia': med.frecuencia,
                    'duracion_dias': med.duracion_dias,
                    'cantidad': med.cantidad_solicitada,
                    'via_administracion': med.via_administracion,
                    'instrucciones': med.instrucciones_especiales
                } for med in medicamentos]
            })
        
        return {
            'success': True,
            'solicitudes': result,
            'total': total,
            'skip': skip,
            'limit': limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Error al obtener solicitudes: {str(e)}'
        )

@router.post("/solicitudes-prescripcion")
def create_solicitud_prescripcion(
    solicitud_data: SolicitudPrescripcionCreate,
    central_db: Session = Depends(get_central_db),
    dept_db: Session = Depends(get_dept_db)
):
    """Crear solicitud de prescripción a farmacia central"""
    try:
        # Validaciones
        if not solicitud_data.medicamentos:
            raise HTTPException(
                status_code=400,
                detail='Debe incluir al menos un medicamento'
            )
        
        # Verificar paciente e historia clínica
        paciente = central_db.query(Paciente).filter(
            Paciente.cod_pac == solicitud_data.cod_pac
        ).first()
        if not paciente:
            raise HTTPException(status_code=404, detail='Paciente no encontrado')
        
        historia = central_db.query(HistoriaClinica).filter(
            HistoriaClinica.cod_hist == solicitud_data.cod_hist
        ).first()
        if not historia:
            raise HTTPException(status_code=404, detail='Historia clínica no encontrada')
        
        # Verificar empleado
        empleado = dept_db.query(Empleado).filter(
            Empleado.id_emp == solicitud_data.id_emp_prescriptor
        ).first()
        if not empleado:
            raise HTTPException(status_code=404, detail='Empleado no encontrado')
        
        # Crear solicitud
        nueva_solicitud = SolicitudPrescripcion(
            cod_pac=solicitud_data.cod_pac,
            cod_hist=solicitud_data.cod_hist,
            id_cita=solicitud_data.id_cita,
            id_emp_prescriptor=solicitud_data.id_emp_prescriptor,
            diagnostico=solicitud_data.diagnostico,
            observaciones_medicas=solicitud_data.observaciones_medicas,
            urgente=solicitud_data.urgente,
            estado_solicitud='ENVIADA',
            fecha_solicitud=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        dept_db.add(nueva_solicitud)
        dept_db.flush()  # Para obtener el ID
        
        # Agregar medicamentos
        medicamentos_creados = []
        for med_data in solicitud_data.medicamentos:
            detalle = DetalleSolicitudMedicamento(
                id_solicitud=nueva_solicitud.id_solicitud,
                nombre_medicamento=med_data.nombre_medicamento,
                principio_activo=med_data.principio_activo,
                concentracion=med_data.concentracion,
                forma_farmaceutica=med_data.forma_farmaceutica,
                dosis=med_data.dosis,
                frecuencia=med_data.frecuencia,
                duracion_dias=med_data.duracion_dias,
                cantidad_solicitada=med_data.cantidad_solicitada,
                instrucciones_especiales=med_data.instrucciones_especiales,
            )
            dept_db.add(detalle)
            medicamentos_creados.append(detalle)
        
        dept_db.commit()
        
        return {
            'success': True,
            'message': 'Solicitud de prescripción creada exitosamente',
            'data': {
                'id_solicitud': nueva_solicitud.id_solicitud,
                'medicamentos': [med.nombre_medicamento for med in medicamentos_creados]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        dept_db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'Error al crear solicitud de prescripción: {str(e)}'
        )