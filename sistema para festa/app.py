from flask import Flask, request, jsonify, send_file, render_template
import qrcode
import uuid
import sqlite3
import smtplib
from email.message import EmailMessage
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
# Defina o caminho para a pasta temporária de uploads
UPLOAD_FOLDER = 'temp'  # Pasta temporária para os uploads
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Cria o diretório de uploads caso não exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/ingressos')
def ingressos():
    # Conectar ao banco de dados e obter os dados
    conn = sqlite3.connect('ingressos.db')
    cursor = conn.cursor()
    cursor.execute('SELECT codigo, nome, cpf, universitario, promoter, status FROM ingressos')  # Alterar 'estado' para 'status'
    ingressos = cursor.fetchall()  # Pega todos os dados da tabela 'ingressos'
    conn.close()

    # Passar os dados para o template
    return render_template('ingressos.html', ingressos=ingressos)


    # Passar os dados para o template
    return render_template('ingressos.html', ingressos=ingressos)


# Simulando integração Pix com valor fixo para o exemplo
def gerar_pix(valor, nome_completo):
    # Aqui deveria estar sua integração real com a API Gerencianet
    # Vamos simular uma URL fictícia de pagamento
    txid = str(uuid.uuid4())
    return {
        "pix_url": f"https://pix.exemplo.com/{txid}",
        "txid": txid
    }

@app.route('/comprar', methods=['POST'])
def comprar():
    data = request.get_json()
    nome = data.get('nome')
    cpf = data.get('cpf')
    universitario = data.get('universitario', False)

    valor = 5 if universitario else 10

    # Simula geração de Pix
    pagamento = gerar_pix(valor, nome)

    # Salva no banco com o código do Pix (txid)
    conn = sqlite3.connect('ingressos.db')
    cursor = conn.cursor()
    cursor.execute(''' 
        INSERT INTO ingressos (codigo, nome, cpf, universitario)
        VALUES (?, ?, ?, ?)
    ''', (pagamento["txid"], nome, cpf, universitario))
    conn.commit()
    conn.close()

    return jsonify({
        "pix_url": pagamento["pix_url"],
        "txid": pagamento["txid"]
    })

@app.route('/confirmar/<txid>', methods=['GET'])
def confirmar_pagamento(txid):
    # Aqui você deveria consultar a API Pix pra verificar se o pagamento foi feito.
    # Para o exemplo, vamos assumir que sim.

    # Buscar dados do ingresso
    conn = sqlite3.connect('ingressos.db')
    cursor = conn.cursor()
    cursor.execute('SELECT nome FROM ingressos WHERE codigo = ?', (txid,))
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        nome = resultado[0]
        qr_filename = f'{txid}_ingresso.png'
        if not os.path.exists(qr_filename):
            img = qrcode.make(txid)
            img.save(qr_filename)

        return send_file(qr_filename, mimetype='image/png')

    return 'Código não encontrado.', 404

# Rota para o formulário de cadastro universitário
@app.route('/universitario', methods=['GET', 'POST'])
def universitario():
    mensagem_sucesso = None  # Inicializa a variável para a mensagem de sucesso

    if request.method == 'POST':
        # Coleta os dados do formulário
        nome = request.form['nome']
        cpf = request.form['cpf']
        ra = request.form['ra']
        email_user = request.form['email']
        foto = request.files['foto_ra']

        if foto:
            # Salvando a foto do RA
            filename = secure_filename(foto.filename)
            caminho_foto = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            foto.save(caminho_foto)
        else:
            return "Erro: nenhuma imagem enviada."

        # Prepara e envia o e-mail
        msg = EmailMessage()
        msg['Subject'] = f"[JB012] Verificação de RA - {nome}"
        msg['From'] = "seu_email@gmail.com"  # Coloque o seu e-mail de envio aqui
        msg['To'] = "bielleite59@gmail.com"
        msg.set_content(f"""
        Nome: {nome}
        CPF: {cpf}
        RA: {ra}
        E-mail: {email_user}
        """)

        with open(caminho_foto, 'rb') as f:
            msg.add_attachment(f.read(), maintype='image', subtype='jpeg', filename=filename)

        # Envio do e-mail via Gmail (certifique-se de usar senha de aplicativo)
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login('bielleite59@gmail.com', 'jqhk ydmz uurf afnk')  # Substitua pela sua senha de app
                smtp.send_message(msg)
            os.remove(caminho_foto)  # Apaga a imagem após o envio
            mensagem_sucesso = "Seu formulário foi enviado com sucesso!"  # Define a mensagem de sucesso
        except Exception as e:
            mensagem_sucesso = f"Erro ao enviar o e-mail: {str(e)}"  # Caso ocorra erro no envio

    # Renderiza o formulário e passa a mensagem de sucesso (se houver)
    return render_template('universitario.html', mensagem_sucesso=mensagem_sucesso)



import sqlite3
from email.message import EmailMessage
import smtplib
import os
from werkzeug.utils import secure_filename
from flask import render_template, request

# Rota para o formulário de cadastro do promoter
@app.route('/promoter', methods=['GET', 'POST'])
def promoter():
    mensagem_sucesso = None  # Inicializa a variável para a mensagem de sucesso

    if request.method == 'POST':
        # Coleta os dados do formulário
        nome = request.form['nome']
        cpf = request.form['cpf']
        email_user = request.form['email']
        instagram_link = request.form['instagram']  # Link do Instagram
        foto = request.files['foto_ra']  # Foto do promoter

        if foto:
            # Salvando a foto do promoter
            filename = secure_filename(foto.filename)
            caminho_foto = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            foto.save(caminho_foto)
        else:
            return "Erro: nenhuma imagem enviada."

        # Inserção no banco de dados
        try:
            conn = sqlite3.connect('ingressos.db')
            cursor = conn.cursor()

            # Inserindo os dados do promoter na tabela 'ingressos', sem RA
            cursor.execute('''
                INSERT INTO ingressos (nome, cpf, email, universitario, promoter, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nome, cpf, email_user, False, True, 'Pendente'))  # Inserindo com status 'Pendente'
            conn.commit()
            conn.close()

        except Exception as e:
            mensagem_sucesso = f"Erro ao salvar no banco de dados: {str(e)}"
            return render_template('promoter.html', mensagem_sucesso=mensagem_sucesso)

        # Prepara e envia o e-mail
        msg = EmailMessage()
        msg['Subject'] = f"[JB012] Verificação de Promoter - {nome}"
        msg['From'] = "seu_email@gmail.com"  # Coloque o seu e-mail de envio aqui
        msg['To'] = "bielleite59@gmail.com"
        msg.set_content(f"""
        Nome: {nome}
        CPF: {cpf}
        E-mail: {email_user}
        Instagram: {instagram_link}
        """)

        with open(caminho_foto, 'rb') as f:
            msg.add_attachment(f.read(), maintype='image', subtype='jpeg', filename=filename)

        # Envio do e-mail via Gmail (certifique-se de usar senha de aplicativo)
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login('bielleite59@gmail.com', 'jqhk ydmz uurf afnk')  # Substitua pela sua senha de app
                smtp.send_message(msg)
            os.remove(caminho_foto)  # Apaga a imagem após o envio
            mensagem_sucesso = "Seu formulário foi enviado com sucesso!"  # Define a mensagem de sucesso
        except Exception as e:
            mensagem_sucesso = f"Erro ao enviar o e-mail: {str(e)}"  # Caso ocorra erro no envio

    # Renderiza o formulário e passa a mensagem de sucesso (se houver)
    return render_template('promoter.html', mensagem_sucesso=mensagem_sucesso)

if __name__ == '__main__':
    app.run(debug=True)
