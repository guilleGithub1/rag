from fastapi import FastAPI
from routes import user as user_routes
from routes import resumen as resumen_routes
from config.database import DatabaseManager
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluye los enrutadores (routers) definidos en la carpeta routes
app.include_router(resumen_routes.router)


@app.get("/")
async def root():
    return {"message": "API Funcionoooo!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)