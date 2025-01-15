from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Cambia esto por una clave secreta unica
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

#           MODELOS 

class Abonado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    N_ABONADO = db.Column(db.String(6), nullable=False, unique=True)
    CONTRASENA = db.Column(db.String(6), nullable=False)
    OLT = db.Column(db.String(2), nullable=True)
    INTERFACE = db.Column(db.String(4), nullable=True)
    ONU = db.Column(db.Integer, nullable=True)
    MARCA = db.Column(db.String(8), nullable=True)
    MAC = db.Column(db.String(22), nullable=True)
    MAC_ = db.Column(db.String(22), nullable=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#  RUTAS 

@app.route('/')
@login_required  # Protege la página de inicio
def index():
    abonados = Abonado.query.all()
    return render_template('index.html', abonados=abonados)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Nombre de usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('login'))

# Ruta para buscar un abonado por su N_ABONADO
@app.route('/search', methods=['GET'])
def search():
    n_abonado = request.args.get('N_ABONADO')  # Captura el valor ingresado en el formulario
    abonado = Abonado.query.filter_by(N_ABONADO=n_abonado).first()  # Busca en la base de datos

    if not abonado:
        return f"No se encontró ningún abonado con N_ABONADO: {n_abonado}"

    # Si se encuentra, redirige a la página de edición del abonado
    return render_template('edit.html', abonado=abonado)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required  # Protege la página de edición
def edit(id):
    abonado = Abonado.query.get_or_404(id)
    if request.method == 'POST':
        abonado.OLT = request.form['OLT']
        abonado.INTERFACE = request.form['INTERFACE']
        abonado.ONU = request.form['ONU']
        abonado.MARCA = request.form['MARCA']
        abonado.MAC = request.form['MAC']

        # Modificar los dos últimos dígitos de la MAC
        if abonado.MAC:
            try:
                # Extraer la MAC y los dos últimos dígitos
                mac_base = abonado.MAC[:-2]  # Todo excepto los últimos dos caracteres
                mac_suffix = abonado.MAC[-2:]  # Los últimos dos caracteres

                # Convertir a hexadecimal
                mac_suffix_dec = int(mac_suffix, 16)

                # Sumar según la marca
                if abonado.MARCA == 'FURUKAWA':
                    mac_suffix_dec += 1
                elif abonado.MARCA == 'BDCOM':
                    mac_suffix_dec += 5
                elif abonado.MARCA == 'LATIC':
                    mac_suffix_dec += 3

                # Asegurar que los dos últimos caracteres estén en formato hexadecimal válido
                mac_suffix_hex = f"{mac_suffix_dec:02X}"

                # Concatenar y actualizar la MAC_
                abonado.MAC_ = mac_base + mac_suffix_hex
            except ValueError:
                flash("El formato de la MAC es inválido.", "danger")
                return redirect(url_for('edit', id=id))
        
        db.session.commit()
        flash('Registro actualizado con éxito.', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', abonado=abonado)

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    abonado = Abonado.query.get_or_404(id)
    
    # Limpiar los campos específicos (poniéndolos en None o en su valor por defecto)
    abonado.OLT = None
    abonado.INTERFACE = None
    abonado.ONU = None
    abonado.MARCA = None
    abonado.MAC = None
    abonado.MAC_ = None

    # Guardar los cambios en la base de datos
    db.session.commit()

    return redirect(url_for('index'))

#         CONFIGURACIÓN INICIAL 

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Asegura que las tablas se creen al iniciar la aplicación
        # Crear un usuario de prueba si no existe
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('admin123')  # Cambia esta contraseña
            db.session.add(admin)
            db.session.commit()

    from os import environ
    port = int(environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)