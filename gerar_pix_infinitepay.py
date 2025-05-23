import requests
import json
import base64

# --- 1. Configurações da InfinitePay ---
# Substitua com suas chaves reais e a URL do ambiente (sandbox ou produção)
INFINITEPAY_API_URL = "https://sandbox-api.infinitepay.io/v1" # Use para testes
# INFINITEPAY_API_URL = "https://api.infinitepay.io/v1" # Use para produção

INFINITEPAY_APP_KEY = "SUA_APP_KEY_AQUI"    # Substitua pela sua App Key
INFINITEPAY_SECRET_KEY = "SUA_SECRET_KEY_AQUI" # Substitua pela sua Secret Key

# --- 2. Preparar Autenticação (Basic Auth) ---
# A InfinitePay usa autenticação Basic com app_key como username e secret_key como password
# Primeiro, codificamos em Base64 para o cabeçalho Authorization
auth_string = f"{INFINITEPAY_APP_KEY}:{INFINITEPAY_SECRET_KEY}"
encoded_auth_string = base64.b64encode(auth_string.encode()).decode()

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {encoded_auth_string}"
}

# --- 3. Dados do Cliente e da Ordem de Pagamento ---
# Estes são dados de exemplo. Em um sistema real, viriam de um formulário ou banco de dados.
customer_data = {
    "name": "Cliente Exemplo",
    "email": "cliente.exemplo@email.com",
    "tax_id": "12345678900", # CPF ou CNPJ (apenas números)
    "phone": "11987654321"
}

# O valor é em centavos, então R$ 25,50 é 2550
amount_in_cents = 2550
order_reference_id = "REF-PIX-001" # Um ID único para sua referência interna
order_description = "Compra de Produto XYZ"

# --- 4. Função para Criar uma Ordem de Pagamento ---
def create_order(customer, amount, reference_id, description):
    order_payload = {
        "amount": amount,
        "customer": customer,
        "reference_id": reference_id,
        "description": description,
        "capture_method": "manual" # Para Pix, geralmente é manual, esperando a cobrança
    }

    order_url = f"{INFINITEPAY_API_URL}/orders"
    print(f"Criando ordem de pagamento em: {order_url}")
    print(f"Payload da ordem: {json.dumps(order_payload, indent=2)}")

    response = requests.post(order_url, headers=headers, data=json.dumps(order_payload))

    if response.status_code == 201:
        order_info = response.json()
        print("Ordem de pagamento criada com sucesso!")
        print(f"ID da Ordem: {order_info['id']}")
        return order_info['id']
    else:
        print(f"Erro ao criar ordem de pagamento: {response.status_code}")
        print(f"Resposta da API: {response.text}")
        return None

# --- 5. Função para Gerar a Cobrança Pix para a Ordem ---
def create_pix_charge(order_id):
    pix_charge_payload = {
        "payment_method": "pix",
        "order_id": order_id
        # Você pode adicionar um expires_in (segundos) ou expires_at (timestamp) aqui
        # Ex: "expires_in": 3600 # Pix expira em 1 hora (3600 segundos)
    }

    charges_url = f"{INFINITEPAY_API_URL}/charges"
    print(f"Criando cobrança Pix em: {charges_url}")
    print(f"Payload da cobrança Pix: {json.dumps(pix_charge_payload, indent=2)}")

    response = requests.post(charges_url, headers=headers, data=json.dumps(pix_charge_payload))

    if response.status_code == 201:
        charge_info = response.json()
        print("\n--- Pix Gerado com Sucesso! ---")
        print(f"ID da Cobrança InfinitePay: {charge_info['id']}")
        print(f"Status da Cobrança: {charge_info['status']}")
        print(f"Valor: R$ {charge_info['amount'] / 100:.2f}")

        # Dados do Pix estão em 'payment_method_data'
        if 'payment_method_data' in charge_info:
            pix_data = charge_info['payment_method_data']
            print("\n--- Dados do Pix ---")
            print(f"QR Code Payload (Copia e Cola): {pix_data.get('qr_code_payload')}")
            print(f"URL do QR Code: {pix_data.get('qr_code_url')}")
            print(f"Expira em: {pix_data.get('expires_at')}")
            print(f"Status do Pix: {pix_data.get('status')}")
        else:
            print("Dados Pix não encontrados na resposta.")
        return charge_info
    else:
        print(f"Erro ao gerar cobrança Pix: {response.status_code}")
        print(f"Resposta da API: {response.text}")
        return None

# --- Fluxo Principal ---
if __name__ == "__main__":
    print("Iniciando processo de geração de Pix com InfinitePay...")

    # 1. Cria a ordem de pagamento
    created_order_id = create_order(
        customer_data,
        amount_in_cents,
        order_reference_id,
        order_description
    )

    if created_order_id:
        # 2. Gera a cobrança Pix para a ordem criada
        pix_charge_details = create_pix_charge(created_order_id)

        if pix_charge_details:
            print("\nProcesso concluído. O Pix InfinitePay foi gerado.")
            # Você pode adicionar lógica aqui para exibir o QR Code,
            # salvar o payload, etc.
        else:
            print("\nFalha ao gerar o Pix InfinitePay.")
    else:
        print("\nFalha ao criar a ordem de pagamento.")