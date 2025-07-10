from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import get_central_db, get_dept_db
from central_models import Paciente
from dept_models import Empleado

# Importar todas las rutas
from routes import patient_routes, employee_routes
from routes import appointment_routes, interconsulta_routes, farmacia_routes
from routes import auth_routes

# ========== LIFESPAN EVENTS (REEMPLAZA on_event) ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación"""
    # ✅ STARTUP
    print("🚀 Iniciando Hospital API...")
    print("=" * 50)
    
    try:
        # Verificar BD Central
        central_db = next(get_central_db())
        pacientes_count = central_db.query(Paciente).count()
        central_db.close()
        print(f"✅ BD Central conectada - {pacientes_count} pacientes registrados")
        
        # Verificar BD Departamento
        dept_db = next(get_dept_db())
        empleados_count = dept_db.query(Empleado).count()
        dept_db.close()
        print(f"✅ BD Departamento conectada - {empleados_count} empleados registrados")
        
        print("🔐 Sistema de autenticación: Activo")
        print("📋 Gestión de pacientes: Activo")
        print("👥 Gestión de empleados: Activo")
        print("📅 Sistema de citas: Activo")
        print("💊 Sistema de farmacia: Activo")
        print("🔄 Interconsultas: Activo")
        print("=" * 50)
        print("🎉 ¡Hospital API iniciado exitosamente!")
        print(f"📖 Documentación disponible en: http://localhost:8000/docs")
        print(f"🔍 Health check en: http://localhost:8000/health")
        
    except Exception as e:
        print(f"❌ Error crítico durante el inicio: {e}")
        print("⚠️ Algunas funcionalidades pueden no estar disponibles")
    
    yield  # ← PUNTO DONDE LA APP ESTÁ CORRIENDO
    
    # ✅ SHUTDOWN
    print("🔄 Cerrando Hospital API...")
    print("💾 Cerrando conexiones de base de datos...")
    print("✅ Hospital API cerrado correctamente")

# ========== CREAR APP CON LIFESPAN ==========
app = FastAPI(
    title="Hospital API", 
    version="1.0.0",
    description="Sistema de Gestión Hospitalaria - API REST",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan  # ← NUEVO MÉTODO SIN WARNINGS
)

# ✅ CORS MEJORADO
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js development
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Backup port
        "http://127.0.0.1:3001",
        "https://your-frontend-domain.com"  # Producción
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ✅ INCLUIR TODAS LAS RUTAS
app.include_router(auth_routes.router, prefix="/auth", tags=["authentication"])
app.include_router(patient_routes.router, prefix="/patients", tags=["patients"])
app.include_router(employee_routes.router, prefix="/employees", tags=["employees"])
app.include_router(appointment_routes.router, prefix="/appointments", tags=["appointments"])
app.include_router(interconsulta_routes.router, prefix="/interconsultas", tags=["interconsultas"])
app.include_router(farmacia_routes.router, prefix="/farmacia", tags=["farmacia"])

@app.get("/")
def read_root():
    """Endpoint principal con información del API"""
    return {
        "message": "🏥 Hospital API funcionando correctamente!", 
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "authentication": "/auth",
            "patients": "/patients", 
            "employees": "/employees", 
            "appointments": "/appointments",
            "interconsultas": "/interconsultas",
            "farmacia": "/farmacia"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "database": {
            "central": "PostgreSQL Cloud",
            "department": "PostgreSQL Local"
        }
    }

@app.get("/health")
def health_check():
    """Endpoint de verificación de salud del sistema"""
    try:
        # Verificar BD Central
        central_db = next(get_central_db())
        pacientes_count = central_db.query(Paciente).count()
        central_db.close()
        central_status = "✅ Connected"
        
        # Verificar BD Departamento
        dept_db = next(get_dept_db())
        empleados_count = dept_db.query(Empleado).count()
        dept_db.close()
        dept_status = "✅ Connected"
        
        return {
            "status": "healthy",
            "timestamp": "2025-07-10T12:00:00Z",
            "databases": {
                "central": {
                    "status": central_status,
                    "patients_count": pacientes_count
                },
                "department": {
                    "status": dept_status,
                    "employees_count": empleados_count
                }
            },
            "services": {
                "authentication": "✅ Active",
                "patient_management": "✅ Active",
                "appointment_system": "✅ Active",
                "pharmacy": "✅ Active"
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-07-10T12:00:00Z"
        }

# ========== MANEJO DE ERRORES GLOBALES ==========
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Endpoint no encontrado",
        "message": "La ruta solicitada no existe",
        "available_endpoints": [
            "/",
            "/health",
            "/docs",
            "/auth/login",
            "/patients/",
            "/employees/",
            "/appointments/"
        ]
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {
        "error": "Error interno del servidor",
        "message": "Ha ocurrido un error inesperado",
        "suggestion": "Verifique los logs del servidor o contacte al administrador"
    }

# ========== EJECUCIÓN PRINCIPAL ==========
if __name__ == "__main__":
    import uvicorn
    print("🏥 Iniciando servidor Hospital API...")
    uvicorn.run(
        "main:app",  # ← FORMATO STRING PARA EVITAR WARNING
        host="0.0.0.0", 
        port=8000,
        reload=True,  # Recarga automática en desarrollo
        log_level="info"
    )