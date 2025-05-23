# ingressos
sistema de ingressos 

# Documentação Completa-InfinitePay

- import base64: Esta nova importação é necessária porque a InfinitePay utiliza Autenticação Basic combinando sua app_key e secret_key codificadas em Base64 no cabeçalho Authorization.
- INFINITEPAY_API_URL: O novo endpoint base para a API da InfinitePay.
- INFINITEPAY_APP_KEY e INFINITEPAY_SECRET_KEY: Suas credenciais específicas para a InfinitePay.
- auth_string e encoded_auth_string: Demonstram como criar a string de autenticação Base64 exigida pela InfinitePay.
- headers: Inclui o cabeçalho Authorization com a string codificada.
- customer_data: Dicionário com informações do cliente. Note que o campo para o documento é tax_id na InfinitePay, não document.
- order_reference_id: Um identificador único que você pode usar internamente para rastrear a ordem. É opcional, mas boa prática.
- create_order(customer, amount, reference_id, description):
    - Propósito: A InfinitePay normalmente exige que você crie uma ordem de pagamento (/orders) antes de gerar uma cobrança específica (como Pix). Esta ordem representa a transação.
    - order_payload: Contém os detalhes da ordem, incluindo o cliente, valor, e uma descrição. O capture_method: "manual" é comum para Pix, indicando que a cobrança será gerada posteriormente.
    - requests.post(order_url, ...): Envia a requisição para criar a ordem.
- create_pix_charge(order_id):
    - Propósito: Esta função cria a cobrança Pix (/charges) associada a uma order_id existente.
    - pix_charge_payload: Define o payment_method como "pix" e associa à order_id.
    - Processamento da Resposta: A resposta da InfinitePay para Pix contém os dados em payment_method_data, que inclui qr_code_payload (o "copia e cola") e qr_code_url (o link da imagem do QR Code).