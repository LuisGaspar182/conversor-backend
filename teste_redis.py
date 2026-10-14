import redis

# Conectando ao Redis rodando no Docker
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Cadastrando as taxas iniciais (1 USD vale...)
r.set('USD', 1)
r.set('BRL', 5)
r.set('ARS', 700)

# Buscando os valores para confirmar se gravou certinho
print("Taxa USD:", r.get('USD'))
print("Taxa BRL:", r.get('BRL'))
print("Taxa ARS:", r.get('ARS'))
