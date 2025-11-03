from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
app = Flask(__name__)

app.secret_key = 'tu_clave_secreta'  # Necesario para sesiones

db_config = {
    "host": "localhost",
    "port": '3308',  # Puerto por defecto de MySQL
    "user": "root",
    "password": "root",
    "database": "Porfolio"
}

# Aseguramos que la conexión use UTF-8 para manejar correctamente nombres con ñ
db_config.update({
    "charset": "utf8mb4",
    "use_unicode": True,
})


def get_db_connection():
    return mysql.connector.connect(**db_config)


@app.route('/')
def home():
    # Pasamos sólo el estado de sesión (logueado o no). No se mostrará el nombre.
    logged_in = session.get('logged_in', False)
    return render_template('index.html', logged_in=logged_in)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        # Intentamos conectar a la base de datos y buscar el usuario en la tabla Users
        conn = None
        cursor = None
        result = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # La tabla en tu SQL es `Users` con columnas `Email` y `Contraseña`.
            cursor.execute(
                "SELECT Email FROM `Users` WHERE Email=%s AND `Contraseña`=%s",
                (email, password),
            )
            result = cursor.fetchone()
        except mysql.connector.Error as e:
            # No mostramos notificaciones al usuario; registramos en consola para debug
            print('DB error:', e)
            result = None
        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn:
                    conn.close()
            except Exception:
                pass
        if result:
            # Marcamos la sesión como iniciada, pero NO guardamos ni mostramos el nombre
            session['logged_in'] = True
            # Al iniciar sesión redirigimos al área de administración
            return redirect(url_for("admin_index"))
    # Si GET o fallo en POST, mostramos el formulario de login
    return render_template("login.html")


@app.route('/logout')
def logout():
    # Eliminar la información de sesión y redirigir a home
    session.pop('logged_in', None)
    return redirect(url_for('home'))


@app.route('/admin')
def admin_index():
    # Si no está logueado, redirigimos al home público
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    # Mostrar la plantilla de administración
    return render_template('index_admin.html')


if __name__ == '__main__':
    app.run(debug=True)
