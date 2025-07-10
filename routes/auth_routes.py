from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from database import get_dept_db
from dept_models import Empleado, UsuarioSistema, RolEmpleado
from auth import verify_password, create_access_token, verify_token, hash_password

router = APIRouter()

# ===============================================
# SCHEMAS DE AUTENTICACIÓN
# ===============================================
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    role: str
    department: str
    email: str
    permissions: Optional[dict] = None

# ===============================================
# ENDPOINTS DE AUTENTICACIÓN
# ===============================================

@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_dept_db)):
    """Autenticar usuario y generar token JWT"""
    try:
        # Buscar usuario por email en la tabla de usuarios del sistema
        usuario_sistema = db.query(UsuarioSistema).filter(
            UsuarioSistema.cuenta_activa == True
        ).join(Empleado).filter(
            Empleado.email_emp == login_data.email
        ).first()
        
        if not usuario_sistema:
            # Intentar login con credenciales demo
            if login_data.email == "admin@hospital.com" and login_data.password == "123456":
                return create_demo_login_response()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o cuenta inactiva"
            )
        
        # Verificar contraseña
        if not verify_password(login_data.password, usuario_sistema.password_hash):
            # Incrementar intentos fallidos
            usuario_sistema.intentos_fallidos += 1
            
            # Bloquear cuenta después de 5 intentos
            if usuario_sistema.intentos_fallidos >= 5:
                usuario_sistema.cuenta_activa = False
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Cuenta bloqueada por múltiples intentos fallidos"
                )
            
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña incorrecta"
            )
        
        # Reset intentos fallidos en login exitoso
        usuario_sistema.intentos_fallidos = 0
        from datetime import datetime
        usuario_sistema.ultimo_acceso = datetime.utcnow()
        db.commit()
        
        # Obtener datos del empleado y rol
        empleado = usuario_sistema.empleado
        rol = empleado.rol if empleado.rol else None
        
        # Crear token JWT
        access_token = create_access_token(data={
            "sub": str(empleado.id_emp),
            "username": usuario_sistema.username,
            "role": rol.nombre_rol if rol else "USUARIO",
            "dept_id": empleado.id_dept
        })
        
        # Preparar respuesta del usuario
        user_data = {
            "id": empleado.id_emp,
            "username": usuario_sistema.username,
            "name": f"{empleado.nom_emp} {empleado.apellido_emp}",
            "role": rol.nombre_rol if rol else "USUARIO",
            "department": empleado.departamento.nom_dept if empleado.departamento else "Sin departamento",
            "email": empleado.email_emp,
            "especialidad": empleado.especialidad_medica,
            "numero_licencia": empleado.numero_licencia,
            "permissions": rol.permisos_sistema if rol else {}
        }
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno durante autenticación: {str(e)}"
        )

def create_demo_login_response():
    """Crear respuesta de login para usuario demo"""
    # Crear token demo
    access_token = create_access_token(data={
        "sub": "demo_user",
        "username": "admin",
        "role": "MEDICO_ESPECIALISTA",
        "dept_id": 1
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": 999,
            "username": "admin",
            "name": "Dr. Admin Demo",
            "role": "MEDICO_ESPECIALISTA",
            "department": "Cardiología",
            "email": "admin@hospital.com",
            "especialidad": "Cardiología Intervencionista",
            "numero_licencia": "DEMO123456",
            "permissions": {
                "puede_prescribir": True,
                "puede_ver_historias": True,
                "puede_modificar_historias": True,
                "puede_agendar_citas": True,
                "puede_generar_reportes": True
            }
        }
    }

@router.get("/me", response_model=UserResponse)
def get_current_user(token: str = Depends(verify_token), db: Session = Depends(get_dept_db)):
    """Obtener información del usuario autenticado"""
    try:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado"
            )
        
        # Si es token demo
        if token == "demo_user":
            return {
                "id": 999,
                "username": "admin",
                "name": "Dr. Admin Demo",
                "role": "MEDICO_ESPECIALISTA",
                "department": "Cardiología",
                "email": "admin@hospital.com",
                "permissions": {
                    "puede_prescribir": True,
                    "puede_ver_historias": True,
                    "puede_modificar_historias": True,
                    "puede_agendar_citas": True,
                    "puede_generar_reportes": True
                }
            }
        
        # Buscar empleado por ID del token
        empleado = db.query(Empleado).filter(Empleado.id_emp == int(token)).first()
        if not empleado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Buscar usuario del sistema
        usuario_sistema = db.query(UsuarioSistema).filter(
            UsuarioSistema.id_emp == empleado.id_emp
        ).first()
        
        return {
            "id": empleado.id_emp,
            "username": usuario_sistema.username if usuario_sistema else empleado.cedula,
            "name": f"{empleado.nom_emp} {empleado.apellido_emp}",
            "role": empleado.rol.nombre_rol if empleado.rol else "USUARIO",
            "department": empleado.departamento.nom_dept if empleado.departamento else "Sin departamento",
            "email": empleado.email_emp,
            "permissions": empleado.rol.permisos_sistema if empleado.rol else {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo usuario: {str(e)}"
        )

@router.post("/logout")
def logout():
    """Cerrar sesión (en el frontend se debe eliminar el token)"""
    return {
        "message": "Sesión cerrada exitosamente",
        "success": True
    }

@router.post("/change-password")
def change_password(
    current_password: str,
    new_password: str,
    token: str = Depends(verify_token),
    db: Session = Depends(get_dept_db)
):
    """Cambiar contraseña del usuario autenticado"""
    try:
        if not token or token == "demo_user":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede cambiar contraseña en modo demo"
            )
        
        # Buscar usuario del sistema
        usuario_sistema = db.query(UsuarioSistema).filter(
            UsuarioSistema.id_emp == int(token)
        ).first()
        
        if not usuario_sistema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar contraseña actual
        if not verify_password(current_password, usuario_sistema.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña actual incorrecta"
            )
        
        # Validar nueva contraseña
        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La nueva contraseña debe tener al menos 6 caracteres"
            )
        
        # Actualizar contraseña
        usuario_sistema.password_hash = hash_password(new_password)
        from datetime import datetime
        usuario_sistema.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "Contraseña actualizada exitosamente",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cambiando contraseña: {str(e)}"
        )

@router.post("/register")
def register_user(
    empleado_id: int,
    username: str,
    password: str,
    db: Session = Depends(get_dept_db)
):
    """Registrar nuevo usuario del sistema (solo para administradores)"""
    try:
        # Verificar que el empleado existe
        empleado = db.query(Empleado).filter(Empleado.id_emp == empleado_id).first()
        if not empleado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empleado no encontrado"
            )
        
        # Verificar que no existe usuario para este empleado
        existing_user = db.query(UsuarioSistema).filter(
            UsuarioSistema.id_emp == empleado_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un usuario para este empleado"
            )
        
        # Verificar que el username es único
        existing_username = db.query(UsuarioSistema).filter(
            UsuarioSistema.username == username
        ).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El nombre de usuario ya está en uso"
            )
        
        # Crear nuevo usuario
        from datetime import datetime
        import secrets
        
        nuevo_usuario = UsuarioSistema(
            id_emp=empleado_id,
            username=username,
            password_hash=hash_password(password),
            salt=secrets.token_hex(16),
            fecha_creacion=datetime.utcnow(),
            ultimo_acceso=None,
            intentos_fallidos=0,
            cuenta_activa=True,
            token_recuperacion=None,
            token_expiracion=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        
        return {
            "message": "Usuario registrado exitosamente",
            "success": True,
            "user_id": nuevo_usuario.id_usuario,
            "username": username,
            "empleado": f"{empleado.nom_emp} {empleado.apellido_emp}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registrando usuario: {str(e)}"
        )

@router.get("/users")
def get_all_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_dept_db)
):
    """Obtener lista de usuarios del sistema (solo para administradores)"""
    try:
        usuarios = db.query(UsuarioSistema).join(Empleado).offset(skip).limit(limit).all()
        
        result = []
        for usuario in usuarios:
            result.append({
                "id_usuario": usuario.id_usuario,
                "username": usuario.username,
                "empleado": f"{usuario.empleado.nom_emp} {usuario.empleado.apellido_emp}",
                "email": usuario.empleado.email_emp,
                "departamento": usuario.empleado.departamento.nom_dept if usuario.empleado.departamento else None,
                "rol": usuario.empleado.rol.nombre_rol if usuario.empleado.rol else None,
                "cuenta_activa": usuario.cuenta_activa,
                "ultimo_acceso": usuario.ultimo_acceso.isoformat() if usuario.ultimo_acceso else None,
                "fecha_creacion": usuario.fecha_creacion.isoformat() if usuario.fecha_creacion else None
            })
        
        return {
            "success": True,
            "total": len(result),
            "users": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo usuarios: {str(e)}"
        )