from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Abonado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    N_ABONADO = db.Column(db.String(6), nullable=False, unique=True)
    CONTRASENA = db.Column(db.String(6), nullable=False)
    OLT = db.Column(db.String(6), nullable=True)
    INTERFACE = db.Column(db.String(4), nullable=True)
    ONU = db.Column(db.Integer, nullable=True)
    MAC = db.Column(db.String(22), nullable=True)

# Inicializa la base de datos y carga los datos
with app.app_context():
    db.create_all()  # Crea las tablas si no existen


@app.route('/')
def index():
    abonados = Abonado.query.all()
    return render_template('index.html', abonados=abonados)

@app.route('/search', methods=['GET'])
def search():
    n_abonado = request.args.get('N_ABONADO')

    # Validar que N_ABONADO tenga entre 5 y 6 dígitos
    if not n_abonado.isdigit() or not (5 <= len(n_abonado) <= 6):
        return "Error: N_ABONADO debe tener entre 5 y 6 dígitos numéricos.", 400

    abonado = Abonado.query.filter_by(N_ABONADO=n_abonado).first()
    if not abonado:
        return f"No se encontró ningún abonado con N_ABONADO: {n_abonado}"
    return render_template('edit.html', abonado=abonado)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    abonado = Abonado.query.get_or_404(id)
    if request.method == 'POST':
        try:
            onu_value = int(request.form['ONU'])
            if onu_value > 128:
                raise ValueError("el numero maximo de ONU es 128.")
            abonado.ONU = onu_value
        except ValueError as e:
            return f"Error: {e}"

        abonado.OLT = request.form['OLT']
        abonado.INTERFACE = request.form['INTERFACE']
        abonado.MAC = request.form['MAC']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', abonado=abonado)

if __name__ == '__main__':
    from os import environ
    port = int(environ.get('PORT', 5000))  # Usa el puerto asignado por Render o 5000 por defecto
    app.run(host='0.0.0.0', port=port)

