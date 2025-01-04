from fastapi import FastAPI
from routes import user as user_routes
from routes import resumen as resumen_routes
from config.database import DatabaseManager

app = FastAPI()

# Incluye los enrutadores (routers) definidos en la carpeta routes
app.include_router(resumen_routes.router)


@app.get("/")
async def root():
    return {"message": "API Funcionoooo!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)