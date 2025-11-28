from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

app.secret_key = 'tu_clave_secreta'

db_config = {
    "host": "localhost",
    "port": '3308',
    "user": "root",
    "password": "root",
    "database": "Porfolio"
}

db_config.update({
    "charset": "utf8mb4",
    "use_unicode": True,
})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'imgs')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    return mysql.connector.connect(**db_config)

def get_projects():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, Titulo, Contenido, fecha, Orientacion FROM Proyectos ORDER BY id DESC")
        rows = cursor.fetchall()
        projects = []
        for r in rows:
            projects.append({
                'id': r.get('id'),
                'titulo': r.get('Titulo'),
                'contenido': r.get('Contenido'),
                'fecha': r.get('fecha'),
                'orientacion': r.get('Orientacion'),
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

def get_experiencias():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, Lugar, Tipo, Fecha_inicio, Fecha_fin, Descripcion, imagen FROM Experiencias ORDER BY Fecha_inicio DESC")
        rows = cursor.fetchall()
        experiencias = []
        for r in rows:
            experiencias.append({
                'id': r.get('id'),
                'lugar': r.get('Lugar'),
                'tipo': r.get('Tipo'),
                'fecha_inicio': r.get('Fecha_inicio'),
                'fecha_fin': r.get('Fecha_fin'),
                'descripcion': r.get('Descripcion'),
                'imagen': r.get('imagen'),
            })
        return experiencias
    except Exception as e:
        print('DB error get_experiencias:', e)
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
    logged_in = session.get('logged_in', False)
    projects = get_projects()
    experiencias = get_experiencias()
    return render_template('index.html', logged_in=logged_in, projects=projects, experiencias=experiencias)

@app.route('/admin')
def admin_index():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    projects = get_projects()
    experiencias = get_experiencias()
    return render_template('index_admin.html', projects=projects, experiencias=experiencias, logged_in=True)

@app.route('/projects')
def projects():
    logged_in = session.get('logged_in', False)
    projects = get_projects()
    return render_template('proyectos.html', logged_in=logged_in, projects=projects)

@app.route('/admin/projects')
def admin_projects():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    projects = get_projects()
    return render_template('proyectos_admin.html', projects=projects, logged_in=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = None
        cursor = None
        result = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT Email FROM `Users` WHERE Email=%s AND `Contraseña`=%s",
                (email, password),
            )
            result = cursor.fetchone()
        except mysql.connector.Error as e:
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
            session['logged_in'] = True
            return redirect(url_for("admin_index"))
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/admin/create_projects', methods=['GET', 'POST'])
def create_projects():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        contenido = request.form.get('contenido', '').strip()
        fecha = request.form.get('fecha', '').strip()
        orientacion = request.form.get('orientacion', '').strip()

        if not fecha:
            from datetime import date
            fecha = date.today().isoformat()

        if not orientacion:
            orientacion = 'Otros'

        if not titulo or not contenido:
            return render_template('create_projects.html', logged_in=session.get('logged_in', False))

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            print('Insertando proyecto con:', {'titulo': titulo, 'orientacion': orientacion, 'contenido_len': len(contenido), 'fecha': fecha})
            cursor.execute(
                "INSERT INTO Proyectos (Titulo, Orientacion, Contenido, fecha) VALUES (%s, %s, %s, %s)",
                (titulo, orientacion, contenido, fecha),
            )
            conn.commit()
            return redirect(url_for('admin_projects'))
        except mysql.connector.Error as e:
            import traceback
            traceback.print_exc()
            print('DB error (insert project):', e)
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

    return render_template('create_projects.html', logged_in=session.get('logged_in', False))

@app.route('/admin/create_experiencias', methods=['GET', 'POST'])
def create_experiencias():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    if request.method == 'POST':
        lugar = request.form.get('lugar', '').strip()
        tipo = request.form.get('tipo', '').strip()
        fecha_inicio = request.form.get('fecha_inicio', '').strip()
        fecha_fin = request.form.get('fecha_fin', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        imagen = None

        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(filepath)
                imagen = filename

        if not tipo:
            tipo = 'Laboral'

        if not lugar or not descripcion or not fecha_inicio:
            return render_template('create_experiencias.html', logged_in=session.get('logged_in', False))

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Experiencias (Lugar, Tipo, Fecha_inicio, Fecha_fin, Descripcion, imagen) VALUES (%s, %s, %s, %s, %s, %s)",
                (lugar, tipo, fecha_inicio if fecha_inicio else None, fecha_fin if fecha_fin else None, descripcion, imagen),
            )
            conn.commit()
            return redirect(url_for('admin_index'))
        except mysql.connector.Error as e:
            import traceback
            traceback.print_exc()
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

    return render_template('create_experiencias.html', logged_in=session.get('logged_in', False))

def get_experiencia_by_id(exp_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, Lugar, Tipo, Fecha_inicio, Fecha_fin, Descripcion FROM Experiencias WHERE id=%s", (exp_id,))
        row = cursor.fetchone()
        return row
    except Exception as e:
        print('DB error get_experiencia_by_id:', e)
        return None
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

@app.route('/edit_experiencias', methods=['GET', 'POST'])
def edit_experiencias():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    exp_id = request.args.get('id')
    if not exp_id:
        return redirect(url_for('admin_index'))

    experiencia = get_experiencia_by_id(exp_id)
    if not experiencia:
        return redirect(url_for('admin_index'))

    if request.method == 'POST':
        lugar = request.form.get('lugar', '').strip()
        tipo = request.form.get('tipo', '').strip()
        fecha_inicio = request.form.get('fecha_inicio', '').strip()
        fecha_fin = request.form.get('fecha_fin', '').strip()
        descripcion = request.form.get('descripcion', '').strip()

        if not tipo:
            tipo = 'Laboral'

        if not lugar or not descripcion or not fecha_inicio:
            return render_template('edit_experiencias.html', experiencia=experiencia, logged_in=True)

        fecha_inicio_db = fecha_inicio if fecha_inicio else None
        fecha_fin_db = fecha_fin if fecha_fin else None

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Experiencias SET Lugar=%s, Tipo=%s, Fecha_inicio=%s, Fecha_fin=%s, Descripcion=%s WHERE id=%s",
                (lugar, tipo, fecha_inicio_db, fecha_fin_db, descripcion, exp_id),
            )
            conn.commit()
            return redirect(url_for('admin_index'))
        except mysql.connector.Error as e:
            import traceback
            traceback.print_exc()
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

    return render_template('edit_experiencias.html', experiencia=experiencia, logged_in=True)

def get_project_by_id(project_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, Titulo, Orientacion, Contenido, fecha FROM Proyectos WHERE id=%s", (project_id,))
        row = cursor.fetchone()
        return row
    except Exception as e:
        print('DB error get_project_by_id:', e)
        return None
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

@app.route('/edit_projects', methods=['GET', 'POST'])
def edit_projects():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    project_id = request.args.get('id')
    if not project_id:
        return redirect(url_for('admin_projects'))

    project = get_project_by_id(project_id)
    if not project:
        return redirect(url_for('admin_projects'))

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        orientacion = request.form.get('orientacion', '').strip()
        contenido = request.form.get('contenido', '').strip()
        fecha = request.form.get('fecha', '').strip()

        if not orientacion:
            orientacion = 'Otros'
        if not fecha:
            from datetime import date
            fecha = date.today().isoformat()

        if not titulo or not contenido:
            return render_template('edit_projects.html', project=project, logged_in=True)

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Proyectos SET Titulo=%s, Orientacion=%s, Contenido=%s, fecha=%s WHERE id=%s",
                (titulo, orientacion, contenido, fecha, project_id),
            )
            conn.commit()
            return redirect(url_for('admin_projects'))
        except mysql.connector.Error as e:
            import traceback
            traceback.print_exc()
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

    return render_template('edit_projects.html', project=project, logged_in=True)

if __name__ == '__main__':
    app.run(debug=True)
