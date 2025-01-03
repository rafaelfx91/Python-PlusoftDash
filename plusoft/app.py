from flask import Flask, render_template, request, redirect, url_for,session
import mysql.connector
from datetime import datetime
import socket
import os
import logging

# Configure os logs no início do arquivo
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, static_folder='templates')

# Configuração de chave secreta
app.config['SECRET_KEY'] = os.urandom(24)  # Geração automática de chave secreta

# Função para conectar ao banco de dados MySQL
def conectar_banco():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="123",  # Atualize com a sua senha do MySQL
            database="campanhas"  # Nome do banco de dados
        )
        return db
    except mysql.connector.Error as err:
        app.logger.error(f"Erro ao conectar ao banco de dados: {str(err)}")
        return None

# Página inicial com formulário de login
@app.route('/')
def index():
    return render_template("index.html")

# Rota para processar login
@app.route('/login', methods=['POST'])
def login():
    usuario = request.form['usuario']
    senha = request.form['senha']
    try:
        conn = conectar_banco()
        cursor = conn.cursor(dictionary=True)  # Dicionário para obter colunas por nome

        # Verificar credenciais no banco de dados
        query = "SELECT * FROM cad_validacao WHERE usuario = %s AND senha = %s AND ativo = 1"
        cursor.execute(query, (usuario, senha))
        user = cursor.fetchone()

        if user:
            # Registrar login
            ip = request.remote_addr or socket.gethostbyname(socket.gethostname())
            status = 1  # Login bem-sucedido
            registro_query = """
                INSERT INTO registro_login (cod_usuario, ip, status) 
                VALUES (%s, %s, %s)
            """
            cursor.execute(registro_query, (user['cod'], ip, status))
            conn.commit()
            
            # Salvar informações na sessão 
            session['logged_in'] = True 
            session['nome'] = user['nome'] 
            session['cod_usuario'] = user['cod']
            
            conn.close()

            # Redirecionar para a página de home
            return redirect(url_for('home', nome=user['nome']))
        else:
            return redirect(url_for('index'))  # Redirecionar novamente após mensagem de erro
    except mysql.connector.Error as err:
        app.logger.error(f"Erro ao processar o login: {str(err)}")
        return redirect(url_for('index'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Página de Home após login
@app.route('/home') 
def home(): 
    if 'logged_in' in session and session['logged_in']: 
        nome = session['nome'] 
        return render_template("home.html", nome=nome) 
    else: 
        return redirect(url_for('index'))

#roda de loggout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
