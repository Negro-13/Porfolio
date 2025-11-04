from flask import Flask, render_template, request, redirect, url_for, session, flash
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


def get_projects():
    """Devuelve una lista de proyectos desde la base de datos.
    Cada proyecto es un dict con claves: id, titulo, contenido, fecha.
    En caso de error devuelve lista vacía.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        # Usamos un cursor que devuelva diccionarios para facilitar la plantilla
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, Titulo, Contenido, fecha FROM Proyectos ORDER BY id DESC")
        rows = cursor.fetchall()
        projects = []
        for r in rows:
            projects.append({
                'id': r.get('id'),
                'titulo': r.get('Titulo'),
                'contenido': r.get('Contenido'),
                'fecha': r.get('fecha'),
            })
        return projects
    except Exception as e:
        print('DB error get_projects:', e)
        return []
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


@app.route('/')
def home():
    # Pasamos sólo el estado de sesión (logueado o no). No se mostrará el nombre.
    logged_in = session.get('logged_in', False)
    # Obtener proyectos y pasarlos a la plantilla pública
    projects = get_projects()
    return render_template('index.html', logged_in=logged_in, projects=projects)

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
    # Obtener proyectos y mostrarlos en el panel de administración
    projects = get_projects()
    return render_template('index_admin.html', projects=projects, logged_in=True)

@app.route('/admin/projects_edits')
def edit_projects():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    return render_template('projects_edits.html')

@app.route('/admin/create_projects', methods=['GET', 'POST'])
def create_projects():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    # Si vienen datos vía POST, los guardamos en la base de datos
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        contenido = request.form.get('contenido', '').strip()
        fecha = request.form.get('fecha', '').strip()

        # Si no se envió fecha, usar la fecha de hoy
        if not fecha:
            from datetime import date
            fecha = date.today().isoformat()

        # Validación mínima
        if not titulo or not contenido:
            flash('El título y el contenido son obligatorios.', 'danger')
            return render_template('create_projects.html', logged_in=session.get('logged_in', False))

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Para depuración imprimimos los parámetros que vamos a insertar
            print('Insertando proyecto con:', {'titulo': titulo, 'contenido_len': len(contenido), 'fecha': fecha})
            cursor.execute(
                "INSERT INTO Proyectos (Titulo, Contenido, fecha) VALUES (%s, %s, %s)",
                (titulo, contenido, fecha),
            )
            conn.commit()
            flash('Proyecto creado correctamente.', 'success')
            # Redirigir al panel admin al terminar
            return redirect(url_for('admin_index'))
        except mysql.connector.Error as e:
            # Mostrar error en consola y a través de flash para facilitar debug durante el desarrollo
            import traceback
            traceback.print_exc()
            print('DB error (insert project):', e)
            flash(f'Error al guardar en la base de datos: {e}', 'danger')
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

    # GET: mostrar el formulario
    return render_template('create_projects.html', logged_in=session.get('logged_in', False))

if __name__ == '__main__':
    app.run(debug=True)
