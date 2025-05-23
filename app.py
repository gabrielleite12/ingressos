import uuid
from flask import Flask, request, jsonify, send_file, render_template, redirect
import qrcode
from reportlab.pdfgen import canvas
import sqlite3
import smtplib
from email.message import EmailMessage
from reportlab.lib.pagesizes import letter
from werkzeug.utils import secure_filename
import os
import smtplib
import ssl


QR_CODE_DIR = 'static/qr_codes/'

app = Flask(__name__)
# Defina o caminho para a pasta temporária de uploads
UPLOAD_FOLDER = 'temp'  # Pasta temporária para os uploads
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Cria o diretório de uploads caso não exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
@app.route('/')
def index():
    return render_template('index.html')


def gerar_pdf(nome, cpf, txid, qr_code_path, logo_path):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import white, black
    from reportlab.pdfgen import canvas

    pdf_path = f"ingresso_{txid}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Fundo preto
    c.setFillColor(black)
    c.rect(0, 0, width, height, fill=1)

    # Logo grande centralizado no topo (300x300)
    logo_width, logo_height = 300, 300
    logo_x = (width - logo_width) / 2
    logo_y = height - logo_height - 20
    c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height, mask='auto')

    # Texto branco e menor
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 12)

    # Informações (nome, cpf, txid) centralizadas uma abaixo da outra
    info_y = logo_y - 30
    c.drawCentredString(width / 2, info_y, f"Nome: {nome}")
    c.drawCentredString(width / 2, info_y - 20, f"CPF: {cpf}")
    c.drawCentredString(width / 2, info_y - 40, f"TXID: {txid}")

    # QR Code centralizado na metade inferior da página
    qr_size = 200
    qr_x = (width - qr_size) / 2
    qr_y = (height / 2) - (qr_size / 2) - 100
    c.drawImage(qr_code_path, qr_x, qr_y, width=qr_size, height=qr_size, mask='auto')

    c.save()
    return pdf_path



def enviar_email(pdf_path, email_destino):
    from_email = "bielleite59@gmail.com"
    password = "jqhk ydmz uurf afnk"
    to_email = email_destino

    msg = EmailMessage()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Seu Ingresso - Baile JB012"
    msg.set_content("Olá, seu ingresso foi gerado com sucesso. Em anexo, você encontrará o PDF com as informações do seu ingresso.")

    with open(pdf_path, "rb") as f:
        msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=os.path.basename(pdf_path))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(from_email, password)
            server.send_message(msg)
        print(f"Email enviado para {email_destino}")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

@app.route('/comprar', methods=['POST'])
def comprar():
    data = request.get_json()
    nome = data.get('nome')
    cpf = data.get('cpf')
    email = data.get('email')
    universitario = data.get('universitario', False)
    promoter = data.get('promoter', False)

    valor = 5 if universitario else 10
    pagamento = gerar_pix(valor, nome)

    txid = pagamento["txid"]
    qr_filename = os.path.join(QR_CODE_DIR, f'{txid}_ingresso.png')

    img = qrcode.make(txid)
    img.save(qr_filename)

    conn = sqlite3.connect('ingressos.db')
    cursor = conn.cursor()
    cursor.execute(''' 
    INSERT INTO ingressos (codigo, nome, cpf, email, universitario, promoter, entrada)
    VALUES (?, ?, ?, ?, ?, ?,?)
''', (txid, nome, cpf, email, universitario, promoter, 1))
    conn.commit()
    conn.close()

    return jsonify({
        "pix_url": pagamento["pix_url"],
        "txid": txid,
        "qr_code_url": f"/static/qr_codes/{txid}_ingresso.png"
    })

@app.route('/confirmar/<txid>', methods=['GET'])
def confirmar_pagamento(txid):
    conn = sqlite3.connect('ingressos.db')
    cursor = conn.cursor()
    cursor.execute('SELECT nome, cpf, email FROM ingressos WHERE codigo = ?', (txid,))
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        nome, cpf, email = resultado
        qr_filename = os.path.join(QR_CODE_DIR, f'{txid}_ingresso.png')
        logo_path = os.path.join("static", "logo.png")

        try:
            if not os.path.exists(qr_filename):
                img = qrcode.make(txid)
                img.save(qr_filename)
            else:
                print(f'O QR Code para {txid} já existe.')

            pdf_path = gerar_pdf(nome, cpf, txid, qr_filename, logo_path)
            enviar_email(pdf_path, email)
            return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')

        except Exception as e:
            print(f"Erro ao gerar o PDF ou enviar e-mail: {e}")
            return "Erro ao gerar o PDF ou enviar o e-mail", 500

    return 'Código não encontrado.', 404

def gerar_pix(valor, nome):
    return {
        "pix_url": f"https://example.com/pix/{valor}/{nome}",
        "txid": f"TXID{valor}{nome}"
    }


#para o formulário de cadastro universitário
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


# Conexão com o banco de dados
def get_db_connection():
    conn = sqlite3.connect('ingressos.db')  # Ajuste o caminho do banco de dados
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/ingressos', methods=['GET', 'POST'])
def exibir_ingressos():
    conn = sqlite3.connect('ingressos.db')
    cursor = conn.cursor()

    # Consultando ingressos
    cursor.execute("SELECT codigo, nome, cpf, universitario, promoter, status FROM ingressos")
    ingressos = cursor.fetchall()
    conn.close()

    # Renderizando o template com os ingressos
    return render_template('ingressos.html', ingressos=ingressos)



@app.route('/excluir/<codigo>')
def excluir_ingresso(codigo):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ingressos WHERE codigo = ?", (codigo,))
    conn.commit()
    conn.close()
    return redirect('/ingressos')  # Redireciona para a página de ingressos após exclusão

@app.route('/apagar_tudo', methods=['POST'])
def apagar_tudo():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ingressos")
    conn.commit()
    conn.close()
    return redirect('/ingressos')  # Redireciona para a página de ingressos após apagar tudo

@app.route('/atualizar_status', methods=['POST'])
def atualizar_status():
    conn = sqlite3.connect('ingressos.db')
    cursor = conn.cursor()

    # Para cada ingresso, verificar o novo status enviado
    for ingresso in request.form:
        if ingresso.startswith('status_'):
            # Pega o id do ingresso (ex: 'status_123')
            id_ingresso = ingresso.split('_')[1]
            novo_status = request.form[ingresso]

            # Verifique o novo_status recebido
            print(f"Atualizando ingresso {id_ingresso} com status {novo_status}")  # Debug

            # Atualiza o status no banco de dados
            cursor.execute("UPDATE ingressos SET status = ? WHERE codigo = ?", (novo_status, id_ingresso))
    
    conn.commit()  # Certifique-se de que a transação está sendo salva
    conn.close()

    # Debug para ver se o banco foi alterado
    print("Transação commitada e banco atualizado.")

    return redirect('/ingressos')  # Volta para a página de ingressos


@app.route("/admin")
def painel_admin():
    return render_template("PainelAdm.html")



@app.route('/api/total_pessoas')
def total_pessoas():
    conn = sqlite3.connect('ingressos.db')
    cursor = conn.cursor()

    # Obtem o nome da primeira (e única) tabela no banco
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tabela = cursor.fetchone()
    
    if tabela:
        nome_tabela = tabela[0]
        cursor.execute(f"SELECT COUNT(*) FROM {nome_tabela}")
        total = cursor.fetchone()[0]
    else:
        total = 0  # Nenhuma tabela encontrada

    conn.close()
    return jsonify({'total': total})



@app.route('/api/total_pagantes')
def total_pagantes():
    conn = sqlite3.connect('ingressos.db')
    cursor = conn.cursor()

    # Obtem o nome da primeira tabela existente
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tabela = cursor.fetchone()

    if tabela:
        nome_tabela = tabela[0]
        # Ajustando a consulta para verificar valores 0, NULL, string vazia e 1 para universitario e promoter
        cursor.execute(f"""
            SELECT COUNT(*) FROM {nome_tabela}
            WHERE (universitario != 1 OR universitario IS NULL OR universitario = '')
              AND (promoter != 1 OR promoter IS NULL OR promoter = '')
        """)
        total_pagantes = cursor.fetchone()[0]
    else:
        total_pagantes = 0

    conn.close()
    return jsonify({'total_pagantes': total_pagantes})


@app.route('/api/clientes')
def clientes():
    conn = sqlite3.connect('ingressos.db')
    cursor = conn.cursor()

    # Consultando ingressos
    cursor.execute("SELECT codigo, nome, cpf, universitario, promoter, status FROM ingressos")
    ingressos = cursor.fetchall()
    conn.close()

    # Renderizando o template com os ingressos
    return jsonify([{
        'codigo': cliente[0],
        'nome': cliente[1],
        'cpf': cliente[2],
        'universitario': cliente[3],
        'promoter': cliente[4],
        'status': cliente[5]
    } for cliente in ingressos])


@app.route("/api/promoters")
def listar_promoters():
    conn = sqlite3.connect("ingressos.db")
    cursor = conn.cursor()
    
    # Obtendo todos os promoters com seus status atualizados
    cursor.execute("SELECT codigo, nome, cpf, email, universitario, status FROM ingressos WHERE promoter = 1")
    dados = cursor.fetchall()
    conn.close()

    # Definindo as colunas esperadas
    colunas = ["codigo", "nome", "cpf", "email", "universitario", "status"]
    
    # Convertendo os dados em uma lista de dicionários
    lista = [dict(zip(colunas, linha)) for linha in dados]
    
    return jsonify(lista)  # Retorna os dados atualizados para o frontend



@app.route("/api/atualizarstatus", methods=["POST"])
def atualizarstatuspromoter():
    dados = request.get_json()
    email = dados.get("email")
    novo_status = dados.get("status")

    try:
        conn = sqlite3.connect("ingressos.db")
        cursor = conn.cursor()

        # Atualiza o status
        cursor.execute("UPDATE ingressos SET status = ? WHERE email = ?", (novo_status, email))
        conn.commit()

        # Se for aprovado, gerar txid e comprovante (QR Code fictício)
        if novo_status == "Aprovado":
            cursor.execute("SELECT nome, cpf, universitario, codigo FROM ingressos WHERE email = ?", (email,))
            resultado = cursor.fetchone()

            if resultado:
                nome, cpf, universitario, codigo_existente = resultado

                if not codigo_existente:  # Só gera se ainda não existir
                    txid = str(uuid.uuid4())[:8]

                    # Gerar QR Code
                    qr_filename = os.path.join(QR_CODE_DIR, f'{txid}_ingresso.png')
                    img = qrcode.make(txid)
                    img.save(qr_filename)

                    # Atualiza o código
                    print("Atualizando código para:", txid, "email:", email)
                    cursor.execute("UPDATE ingressos SET codigo = ? WHERE email = ?", (txid, email))
                    conn.commit()

                    conn.close()

                    return jsonify({
                        "sucesso": True,
                        "txid": txid,
                        "qr_code_url": f"/static/qrcodes/{txid}_ingresso.png"
                    })

        conn.close()
        return jsonify({"sucesso": True})
    except Exception as e:
        print("Erro ao atualizar status:", e)
        return jsonify({"sucesso": False})


@app.route('/validar_codigo', methods=['POST'])
def validar_codigo():
    data = request.get_json()
    codigo = data.get('codigo')

    conn = sqlite3.connect('ingressos.db')
    cursor = conn.cursor()

    # Verifica se o código existe e obtém o valor atual da entrada
    cursor.execute("SELECT entrada FROM ingressos WHERE codigo = ?", (codigo,))
    resultado = cursor.fetchone()

    if resultado:
        entrada_atual = resultado[0]

        # Só subtrai se for maior que 0
        if entrada_atual > 0:
            nova_entrada = entrada_atual - 1
            cursor.execute("UPDATE ingressos SET entrada = ? WHERE codigo = ?", (nova_entrada, codigo))
            conn.commit()
            conn.close()
            return jsonify(confirmado=True, restante=nova_entrada)
        else:
            conn.close()
            return jsonify(confirmado=False, motivo="Ingresso já utilizado")
    else:
        conn.close()
        return jsonify(confirmado=False, motivo="Código não encontrado")


if __name__ == '__main__':
    app.run(debug=True)
