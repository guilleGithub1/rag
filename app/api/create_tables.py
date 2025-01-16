from config.database import DatabaseManager

def init_database():
    # Crear instancia del manejador
    db_manager = DatabaseManager()
    
    # Crear tablas
    if db_manager.create_database():
        print("Base de datos creada exitosamente")
    else:
        print("Error al crear la base de datos")

if __name__ == "__main__":
    init_database()