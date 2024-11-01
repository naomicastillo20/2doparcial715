import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import sqlite3
from functools import wraps

# Configuración básica de la aplicación
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Cambia esta clave en producción

# Configuración de Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Conexión a la base de datos SQLite
def conectar_bd():
    db_path = os.path.join(os.path.dirname(__file__), 'cuentas_por_pagar.db')
    return sqlite3.connect(db_path)

# Modelo de Usuario
class User(UserMixin):
    def __init__(self, id, username, password_hash, role):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Carga del usuario desde la base de datos
@login_manager.user_loader
def load_user(user_id):
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()

    if user_data:
        return User(id=user_data[0], username=user_data[1], password_hash=user_data[2], role=user_data[3])
    return None

# Formulario de Login usando Flask-WTF
class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

# Ruta para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Verificar usuario en la base de datos
        with conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM usuarios WHERE username = ?', (username,))
            user_data = cursor.fetchone()

        if user_data:
            user = User(id=user_data[0], username=user_data[1], password_hash=user_data[2], role=user_data[3])
            if user.check_password(password):
                login_user(user)
                flash('Inicio de sesión exitoso', 'success')
                return redirect(url_for('index'))
            else:
                flash('Contraseña incorrecta', 'danger')
        else:
            flash('Usuario no encontrado', 'danger')

    return render_template('login.html', form=form)

def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role != role and current_user.role != 'admin':
                flash('No tienes permiso para acceder a esta página.', 'danger')
                return redirect(url_for('index'))  # Redirige a la página principal
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# Ruta para cerrar sesión
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('login'))

# Ruta principal
@app.route('/')
@login_required
def index():
    # Redirige según el rol
    if current_user.role == 'admin':
        return render_template('index.html', admin=True)
    else:
        return render_template('index.html', admin=False)


# Rutas de proveedores
@app.route('/agregar_proveedor', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def agregar_proveedor():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']
        
        with conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO proveedores (nombre, email, telefono) VALUES (?, ?, ?)', (nombre, email, telefono))
            conn.commit()
        return redirect('/listar_proveedores')
    return render_template('agregar_proveedor.html')

@app.route('/editar_proveedor/<int:proveedor_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editar_proveedor(proveedor_id):
    with conectar_bd() as conn:
        cursor = conn.cursor()
        if request.method == 'POST':
            nombre = request.form['nombre']
            direccion = request.form.get('direccion')
            telefono = request.form.get('telefono')
            email = request.form.get('email')

            cursor.execute('UPDATE proveedores SET nombre=?, direccion=?, telefono=?, email=? WHERE id=?',
                           (nombre, direccion, telefono, email, proveedor_id))
            conn.commit()
            return redirect('/listar_proveedores')
        
        cursor.execute('SELECT * FROM proveedores WHERE id=?', (proveedor_id,))
        proveedor = cursor.fetchone()
    return render_template('editar_proveedor.html', proveedor=proveedor)

@app.route('/eliminar_proveedor/<int:proveedor_id>', methods=['POST'])
@login_required
@role_required('admin')
def eliminar_proveedor(proveedor_id):
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM proveedores WHERE id = ?', (proveedor_id,))
        conn.commit()
    return redirect('/listar_proveedores')

@app.route('/listar_proveedores')
@login_required
@role_required('admin')
def listar_proveedores():
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM proveedores')
        proveedores = cursor.fetchall()
    return render_template('listar_proveedores.html', proveedores=proveedores)

# Rutas de deudas
@app.route('/agregar_deuda', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def agregar_deuda():
    if request.method == 'POST':
        proveedor_id = request.form['proveedor_id']
        monto = request.form['monto']
        fecha_vencimiento = request.form['fecha_vencimiento']

        with conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO deudas (proveedor_id, monto, fecha_vencimiento) VALUES (?, ?, ?)', (proveedor_id, monto, fecha_vencimiento))
            conn.commit()
        return redirect('/listar_deudas')
    return render_template('agregar_deuda.html')

@app.route('/listar_deudas')
@login_required
@role_required('admin')
def listar_deudas():
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM deudas')
        deudas = cursor.fetchall()
    return render_template('listar_deudas.html', deudas=deudas)

@app.route('/editar_deuda/<int:deuda_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editar_deuda(deuda_id):
    with conectar_bd() as conn:
        cursor = conn.cursor()
        if request.method == 'POST':
            proveedor_id = request.form['proveedor_id']
            monto = request.form['monto']
            fecha_vencimiento = request.form['fecha_vencimiento']

            cursor.execute('UPDATE deudas SET proveedor_id=?, monto=?, fecha_vencimiento=? WHERE id=?',
                           (proveedor_id, monto, fecha_vencimiento, deuda_id))
            conn.commit()
            return redirect('/listar_deudas')

        cursor.execute('SELECT * FROM deudas WHERE id=?', (deuda_id,))
        deuda = cursor.fetchone()
    return render_template('editar_deuda.html', deuda=deuda)

@app.route('/eliminar_deuda/<int:deuda_id>', methods=['POST'])
@login_required
@role_required('admin')
def eliminar_deuda(deuda_id):
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM deudas WHERE id = ?', (deuda_id,))
        conn.commit()
    return redirect('/listar_deudas')

# Rutas de facturas
UPLOAD_FOLDER = 'C:\\Users\\naomi\\OneDrive\\Escritorio\\CuentasxPagar-master\\static\\uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/agregar_factura', methods=['GET', 'POST'])
@login_required
def agregar_factura():
    if request.method == 'POST':
        proveedor_id = request.form['proveedor_id']
        monto = request.form['monto']
        fecha = request.form['fecha']
        fecha_vencimiento = request.form['fecha_vencimiento']
        condiciones_pago = request.form['condiciones_pago']

        # Manejo de archivos subidos
        archivo = request.files['archivo']
        if archivo:
            archivo_path = os.path.join(app.config['UPLOAD_FOLDER'], archivo.filename)
            archivo.save(archivo_path)
        else:
            archivo_path = None

        with conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO facturas (proveedor_id, monto, fecha, fecha_vencimiento, condiciones_pago, archivo) VALUES (?, ?, ?, ?, ?, ?)', (proveedor_id, monto, fecha, fecha_vencimiento, condiciones_pago, archivo_path))
            conn.commit()
        return redirect('/listar_facturas')

    return render_template('agregar_factura.html')

@app.route('/editar_factura/<int:factura_id>', methods=['GET', 'POST'])
@login_required
def editar_factura(factura_id):
    with conectar_bd() as conn:
        cursor = conn.cursor()
        if request.method == 'POST':
            proveedor_id = request.form['proveedor_id']
            monto = request.form['monto']
            fecha = request.form['fecha']
            fecha_vencimiento = request.form['fecha_vencimiento']
            condiciones_pago = request.form['condiciones_pago']

            # Manejo de archivos subidos
            archivo = request.files['archivo']
            if archivo:
                archivo_path = os.path.join(app.config['UPLOAD_FOLDER'], archivo.filename)
                archivo.save(archivo_path)
            else:
                archivo_path = None

            cursor.execute('UPDATE facturas SET proveedor_id=?, monto=?, fecha=?, fecha_vencimiento=?, condiciones_pago=?, archivo=? WHERE id=?',
                           (proveedor_id, monto, fecha, fecha_vencimiento, condiciones_pago, archivo_path, factura_id))
            conn.commit()
            return redirect('/listar_facturas')

        cursor.execute('SELECT * FROM facturas WHERE id=?', (factura_id,))
        factura = cursor.fetchone()
    return render_template('editar_factura.html', factura=factura)

@app.route('/eliminar_factura/<int:factura_id>', methods=['POST'])
@login_required
@role_required('admin')
def eliminar_factura(factura_id):
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM facturas WHERE id = ?', (factura_id,))
        conn.commit()
    return redirect('/listar_facturas')

@app.route('/listar_facturas')
@login_required
def listar_facturas():
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM facturas')
        facturas = cursor.fetchall()
    return render_template('listar_facturas.html', facturas=facturas)

@app.route('/listar_pagos')
@login_required
def listar_pagos():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM pagos')
    pagos = cursor.fetchall()
    conn.close()
    return render_template('listar_pagos.html', pagos=pagos)

@app.route('/registrar_pago', methods=['GET', 'POST'])
@login_required
def registrar_pago():
    if request.method == 'POST':
        factura_id = request.form['factura_id']
        monto = request.form['monto']
        fecha = request.form['fecha']
        metodo_pago = request.form['metodo_pago']

        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO pagos (factura_id, monto, fecha, metodo_pago) VALUES (?, ?, ?, ?)', (factura_id, monto, fecha, metodo_pago))
        conn.commit()
        conn.close()
        return redirect('/listar_pagos')

    return render_template('registrar_pago.html')

@app.route('/editar_pago/<int:pago_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editar_pago(pago_id):
    conn = conectar_bd()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        factura_id = request.form['factura_id']
        monto = request.form['monto']
        fecha = request.form['fecha']
        metodo_pago = request.form['metodo_pago']

        cursor.execute('UPDATE pagos SET factura_id=?, monto=?, fecha=?, metodo_pago=? WHERE id=?',
                       (factura_id, monto, fecha, metodo_pago, pago_id))
        conn.commit()
        conn.close()
        return redirect('/listar_pagos')

    cursor.execute('SELECT * FROM pagos WHERE id=?', (pago_id,))
    pago = cursor.fetchone()
    conn.close()
    return render_template('editar_pago.html', pago=pago)

@app.route('/eliminar_pago/<int:pago_id>', methods=['POST'])
@login_required
@role_required('admin')
def eliminar_pago(pago_id):
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM pagos WHERE id = ?', (pago_id,))
    conn.commit()
    conn.close()
    
    return redirect('/listar_pagos')

# Ruta de contacto
@app.route('/contacto')
@login_required
def contacto():
    return render_template('contacto.html')

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)