from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# Configuración de seguridad
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Configuración de encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración de Bearer token
security = HTTPBearer()

def hash_password(password: str) -> str:
    """Encriptar contraseña usando bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña contra hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Crear token JWT de acceso"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verificar y decodificar token JWT"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: no se encontró el usuario",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user_id
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error verificando token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

def decode_token(token: str) -> dict:
    """Decodificar token sin verificar (para inspección)"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def is_token_expired(token: str) -> bool:
    """Verificar si un token ha expirado"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            return datetime.utcnow() > exp_datetime
        return True
    except JWTError:
        return True

def refresh_token(token: str) -> str:
    """Refrescar token si está próximo a expirar"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload.get("exp")
        
        if exp_timestamp:
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            time_until_expiry = exp_datetime - datetime.utcnow()
            
            # Si expira en menos de 2 horas, generar nuevo token
            if time_until_expiry < timedelta(hours=2):
                # Remover timestamp de expiración para crear nuevo token
                new_payload = {k: v for k, v in payload.items() if k != "exp"}
                return create_access_token(new_payload)
        
        return token  # Retornar token original si no necesita refresh
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido para refresh"
        )

# Dependencias de autorización por roles
def require_role(required_roles: list):
    """Crear dependencia que requiere roles específicos"""
    def role_checker(credentials: HTTPAuthorizationCredentials = Depends(security)):
        try:
            token = credentials.credentials
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_role = payload.get("role")
            
            if user_role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Rol insuficiente. Se requiere uno de: {required_roles}"
                )
            
            return payload
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    return role_checker

# Roles predefinidos
ROLES = {
    "DIRECTOR": ["DIRECTOR"],
    "MEDICO": ["DIRECTOR", "MEDICO_ESPECIALISTA", "MEDICO_GENERAL"],
    "ENFERMERO": ["DIRECTOR", "MEDICO_ESPECIALISTA", "MEDICO_GENERAL", "ENFERMERO"],
    "EMPLEADO": ["DIRECTOR", "MEDICO_ESPECIALISTA", "MEDICO_GENERAL", "ENFERMERO", "EMPLEADO"],
    "TODOS": ["DIRECTOR", "MEDICO_ESPECIALISTA", "MEDICO_GENERAL", "ENFERMERO", "EMPLEADO", "PACIENTE"]
}

# Dependencias de autorización comunes
require_director = require_role(ROLES["DIRECTOR"])
require_medico = require_role(ROLES["MEDICO"])
require_enfermero = require_role(ROLES["ENFERMERO"])
require_empleado = require_role(ROLES["EMPLEADO"])
require_authenticated = require_role(ROLES["TODOS"])

def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Obtener información del usuario actual desde el token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "dept_id": payload.get("dept_id"),
            "exp": payload.get("exp")
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )

# Utilidades adicionales
def generate_password_reset_token(user_id: str) -> str:
    """Generar token para reset de contraseña (válido por 1 hora)"""
    expire = datetime.utcnow() + timedelta(hours=1)
    data = {"sub": user_id, "type": "password_reset", "exp": expire}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_password_reset_token(token: str) -> str:
    """Verificar token de reset de contraseña"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if token_type != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token no válido para reset de contraseña"
            )
        
        return user_id
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de reset inválido o expirado"
        )