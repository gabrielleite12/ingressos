import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect("ingressos.db")
cursor = conn.cursor()

# Obter os nomes das colunas
cursor.execute("PRAGMA table_info(ingressos)")
colunas = cursor.fetchall()
nomes_colunas = [coluna[1] for coluna in colunas]
print("Colunas da tabela 'ingressos':")
print(nomes_colunas)

# Buscar e exibir todas as linhas da tabela
cursor.execute("SELECT * FROM ingressos")
linhas = cursor.fetchall()

print("\nDados da tabela 'ingressos':")
for linha in linhas:
    print(dict(zip(nomes_colunas, linha)))  # Mostra como dicionário

conn.close()
