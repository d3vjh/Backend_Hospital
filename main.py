from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routes import auth_routes, patient_routes, employee_routes, appointment_routes

# Crear las tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hospital API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(patient_routes.router, prefix="/patients", tags=["patients"])
app.include_router(employee_routes.router, prefix="/employees", tags=["employees"])
app.include_router(appointment_routes.router, prefix="/appointments", tags=["appointments"])

@app.get("/")
def read_root():
    return {"message": "Hospital API funcionando!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)