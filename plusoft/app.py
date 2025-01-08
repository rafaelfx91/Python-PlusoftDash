from flask import Flask, render_template, request, redirect, url_for,session
import mysql.connector
from unidecode import unidecode
import re
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
            
            # Banco de dados informações para trazer
            # nome
            # email
            # contato
            # nivel_acesso
            #
            # Salvar informações na sessão 
            session['logged_in'] = True 
            session['cod_usuario'] = user['cod']
            session['nome'] = user['nome'] 
            session['email'] = user['email']
            session['contato'] = user['contato']
            session['nivel_acesso'] = user['nivel_acesso']
            
            conn.close()

            # Redirecionar para a página de home
            #return redirect(url_for('home', nome=user['nome']))
            return redirect(url_for('home'))
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
        cod = session['cod_usuario'] 
        nome = session['nome'] 
        email = session['email'] 
        contato = session['contato'] 
        nivel_acesso = session['nivel_acesso'] 

        #formatar o nome para preencher 
        nome_formatado = f"{cod} - {nome}"

        #valida nivel do usuario
        niveldesc = retornaNivel(nivel_acesso)

        return render_template("home.html"
                               ,nome=nome_formatado
                               ,email=email
                               ,contato=contato
                               ,nivel=nivel_acesso 
                               ,niveldesc = niveldesc) 
    else: 
        return redirect(url_for('index'))

#funcao para ver o nivel do colicitante
def retornaNivel(acao):
    if acao == 0:
        return "Solicitante"
    elif acao == 2:
        return "Fabrica"
    elif acao == 4:
        return "Administrador"
    elif acao == 5:
        return "Desenvolvedor"
    else:
        return "Sem definição"
# -- nivel_acesso
#0 - Solicitante
#1 -
#2 - Fabrica
#3 -
#4 - admin
#5 - Dev
#


#pagina do sas
@app.route('/sas')
def sas():
    # Verifica se o usuário está logado
    if 'logged_in' in session and session['logged_in']: 
        nivel_acesso = session.get('nivel_acesso', None)  # Melhor usar .get() para evitar KeyError    
        # Se o nível de acesso não for '0' (pode ser número ou string)
        if nivel_acesso != '0' and nivel_acesso != 0:  # Comparação com '0' e 0 (string e número)
            return render_template("sas.html", nivel=nivel_acesso)
        else:
            # Se o nível de acesso for '0', redireciona para o index
            return redirect(url_for('index')) 
    else:
        # Caso o usuário não esteja logado, redireciona para o index
        return redirect(url_for('index'))


#trata o texto do sas fazendo uma tratativa 
@app.route('/sas', methods=['POST'])
def processar_texto():
    # Captura o texto enviado no formulário
    texto = request.form['input_text']  # 'input_text' é o nome do campo do formulário
    
    # Divide o texto por linha
    linhas = texto.splitlines()
    
    # Processa cada linha
    linhas_processadas = []
    for linha in linhas:
        # Remove espaços e substitui por "_"
        linha_processada = linha.replace(" ", "_")

        # Limita a 60 caracteres
        linha_processada = linha_processada[:60]  # Limita a 60 caracteres
        
        
        # Remove caracteres especiais (apenas permite letras, números e underscores)
        linha_processada = re.sub(r'[^a-zA-Z0-9_]', '', linha_processada)
        
        # Remove acentos
        linha_processada = unidecode(linha_processada)
        
        # Converte para maiúsculas
        linha_processada = linha_processada.upper()
        
        # Remove os underscores no final da linha
        linha_processada = linha_processada.rstrip('_')
        
        linhas_processadas.append(linha_processada)

    # Concatena as linhas processadas em uma string, separadas por nova linha
    resultado = "\n".join(linhas_processadas)
    
    #como o menu usa esse atributo sera passado apenas para preencher no menu
    nivel_acesso = session.get('nivel_acesso', None)

    # Retorna o resultado para a mesma página com o texto processado
    return render_template("sas.html", texto_original=texto
                            ,linhas_processadas=resultado
                            ,nivel=nivel_acesso)





#pagina do sms
@app.route('/sms')
def sms():
    # Verifica se o usuário está logado
    if 'logged_in' in session and session['logged_in']: 
        #nivel_acesso = session.get('nivel_acesso', None)
        nivel_acesso = session['nivel_acesso'] 
        return render_template("sms.html", nivel=nivel_acesso)
    else:
        # Caso o usuário não esteja logado, redireciona para o index
        return redirect(url_for('index'))



#prepara a msg 
@app.route('/sms', methods=['POST'])
def processa_msg():
    nivel_acesso = session['nivel_acesso'] 
    hora_atual = datetime.now().strftime('%H:%M')
    
    # Captura o texto enviado no formulário
    texto = request.form['message']  # 'input_text' é o nome do campo do formulário

    com_acentos = "ÄÅÁÂÀÃäáâàãÉÊËÈéêëèÍÎÏÌíîïìÖÓÔÒÕöóôòõÜÚÛüúûùÇç"
    sem_acentos = "AAAAAAaaaaaEEEEeeeeIIIIiiiiOOOOOoooooUUUuuuuCc"

    # Substitui os caracteres com acentos pelos equivalentes sem acentos
    for i in range(len(com_acentos)):
        texto = texto.replace(com_acentos[i], sem_acentos[i])

    # Remove caracteres especiais usando regex
    texto = re.sub(r'[^a-zA-Z0-9 :+=/{}%.*,!?$@#-]+', '', texto)

    return render_template("sms.html"
                        ,msg=texto
                        ,hora=hora_atual
                        ,nivel=nivel_acesso)








#roda de loggout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
