import sqlite3

# Conecta ao banco de dados (ou cria, caso não exista)
conn = sqlite3.connect('ingressos.db')
cursor = conn.cursor()

# Cria a tabela ingressos, incluindo as colunas RA, email, status, etc.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS ingressos (
        codigo TEXT PRIMARY KEY,
        nome TEXT NOT NULL,
        cpf TEXT NOT NULL,
        ra TEXT NOT NULL,        -- Coluna RA
        email TEXT NOT NULL,     -- Coluna email
        universitario BOOLEAN,
        promoter BOOLEAN,
        status TEXT CHECK(status IN ('Aprovado', 'Pendente', 'Reprovado'))  -- Nova coluna status
    )
''')

# Confirma as alterações e fecha a conexão
conn.commit()
conn.close()

print("Banco de dados criado com sucesso!")
