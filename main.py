from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import get_central_db, get_dept_db  # ← AGREGAR ESTO
from central_models import Paciente  # ← AGREGAR ESTO
from dept_models import Empleado  # ← AGREGAR ESTO
# Importar todas las rutas
from routes import patient_routes, employee_routes
from routes import appointment_routes, interconsulta_routes, farmacia_routes



app = FastAPI(title="Hospital API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ INCLUIR TODAS LAS RUTAS
app.include_router(patient_routes.router, prefix="/patients", tags=["patients"])
app.include_router(employee_routes.router, prefix="/employees", tags=["employees"])

# ✅ NUEVAS RUTAS DE CITAS, INTERCONSULTAS Y FARMACIA
app.include_router(appointment_routes.router, prefix="/appointments", tags=["appointments"])
app.include_router(interconsulta_routes.router, prefix="/interconsultas", tags=["interconsultas"])
app.include_router(farmacia_routes.router, prefix="/farmacia", tags=["farmacia"])

@app.get("/")
def read_root():
    return {
        "message": "Hospital API funcionando!", 
        "endpoints": [
            "/patients", 
            "/employees", 
            "/appointments",
            "/interconsultas",
            "/farmacia",
            "/docs"
        ]
    }

# ========== PRUEBA TEMPORAL DE CONEXIONES ==========
@app.on_event("startup")
async def startup_event():
    print("🚀 Iniciando Hospital API...")
    
    try:
        central_db = next(get_central_db())
        pacientes_count = central_db.query(Paciente).count()
        central_db.close()
        print(f"✅ BD Central conectada - {pacientes_count} pacientes")
        
        dept_db = next(get_dept_db())
        empleados_count = dept_db.query(Empleado).count()
        dept_db.close()
        print(f"✅ BD Departamento conectada - {empleados_count} empleados")
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)