import sqlite3
import os
from werkzeug.security import generate_password_hash

# Función para crear y conectar la base de datos
def conectar_bd():
    db_path = os.path.join(os.path.dirname(__file__), 'cuentas_por_pagar.db')
    return sqlite3.connect(db_path)

# Función para crear las tablas en la base de datos
def crear_bd():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Crear la tabla de proveedores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            direccion TEXT,
            telefono TEXT,
            email TEXT
        )
    ''')
    
    # Crear la tabla de deudas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deudas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER NOT NULL,
            monto REAL NOT NULL,
            fecha_vencimiento DATE NOT NULL,
            descripcion TEXT,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)  
        )
    ''')

    # Crear la tabla de facturas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facturas (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           proveedor_id INTEGER,
           monto REAL,
           fecha TEXT,
           fecha_vencimiento TEXT,
           condiciones_pago TEXT,
           archivo TEXT,
           FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
        )   
    ''')

    # Crear la tabla de pagos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagos (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           factura_id INTEGER,
           monto REAL,
           fecha TEXT,
           metodo_pago TEXT,
           FOREIGN KEY (factura_id) REFERENCES facturas(id)
        )
    ''')

    # Crear la tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'user'))
        )
    ''')
    
    conn.commit()
    conn.close()

# Función para insertar usuarios iniciales
def insertar_usuario_inicial():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Datos del usuario administrador inicial
    admin_username = "admin"
    admin_password = generate_password_hash("admin123")
    admin_role = "admin"
    
    # Inserta el usuario admin si no existe
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (username, password, role) 
        VALUES (?, ?, ?)
    ''', (admin_username, admin_password, admin_role))
    
    # Datos del usuario regular inicial
    user_username = "user"
    user_password = generate_password_hash("user123")
    user_role = "user"
    
    # Inserta el usuario user si no existe
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (username, password, role) 
        VALUES (?, ?, ?)
    ''', (user_username, user_password, user_role))

    # Verificar usuarios creados
    cursor.execute("SELECT * FROM usuarios")
    users = cursor.fetchall()
    print("Usuarios en la base de datos:", users)

    conn.commit()
    conn.close()
    print("Usuarios iniciales creados en la base de datos.")

# Ejecuta la creación de tablas y los usuarios iniciales si no existen
if __name__ == "__main__":
    crear_bd()
    insertar_usuario_inicial()