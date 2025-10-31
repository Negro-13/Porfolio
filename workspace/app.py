from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
app = Flask(__name__)

app.secret_key = 'tu_clave_secreta'  # Necesario para sesiones

db_config = {
    "host": "localhost",
    "port": '3306',  # Puerto por defecto de MySQL
    "user": "root",
    "password": "",
    "database": "Porfolio"
}


def get_db_connection():
    return mysql.connector.connect(**db_config)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
