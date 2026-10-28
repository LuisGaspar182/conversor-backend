import json
import os
from fastapi import FastAPI, HTTPException, status
import redis
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API Conversor de Moedas")

REDIS_URL = os.getenv("REDIS_URL", "redis-cli --tls -u redis://default:gQAAAAAAA5PCAAIgcDFlYzZlYjQ3OTQ5ZjQ0MzVjOTBjNjM3NjZhZTE3NjI1OQ@meet-koi-234434.upstash.io:6379")

# Conexão com o Redis
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Cadastrar uma taxa
@app.post("/taxas/{moeda}/{valor}", status_code=status.HTTP_201_CREATED)
def cadastrar_taxa(moeda: str, valor: float):
    # Validar se a moeda é suportada e se o valor é > 0 (Retornar 400 Bad Request)
    if valor <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valor deve ser maior que zero.")

    # Salvar a taxa no Redis
    r.set(moeda.upper(), valor)
    # Retornar mensagem de sucesso
    return {"message": f"Taxa salva. 1 USD = {valor} {moeda.upper()}"}

# Converter um valor
@app.get("/converter/{valor}/{moeda_origem}/{moeda_destino}")
def converter(valor: float, moeda_origem: str, moeda_destino: str):
    # Validar se valor é > 0, moedas são diferentes e se existem no banco (Erros 400 e 404)
    if valor <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valor deve ser maior que zero.")
    if moeda_origem.upper() == moeda_destino.upper():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Moedas de origem e destino devem ser diferentes.")
    if not r.exists(moeda_origem.upper()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taxa de origem não encontrada.")
    if not r.exists(moeda_destino.upper()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taxa de destino não encontrada.")

    # Buscar as taxas no Redis e aplicar a fórmula matemática
    taxa_origem = float(r.get(moeda_origem.upper()))
    taxa_destino = float(r.get(moeda_destino.upper()))
    convertido = valor * (taxa_destino / taxa_origem)

    # Retornar o JSON com "valor", "moeda_origem", "moeda_destino" e "convertido"
    resultado = {
        "valor": valor,
        "moeda_origem": moeda_origem.upper(),
        "moeda_destino": moeda_destino.upper(),
        "convertido": round(convertido, 2)
    }
    # Gravar essa conversão no histórico do Redis
    r.lpush("historico", json.dumps(resultado))
    r.ltrim("historico", 0, 4)  # Mantém apenas as últimas 5 conversões
    return resultado

# Histórico das últimas 5 conversões
@app.get("/conversoes")
def historico():
    # Buscar a lista das últimas conversões no Redis
    historico = r.lrange("historico", 0, 4)
    # Retornar erro 404 caso o histórico esteja vazio
    if not historico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma conversão encontrada.")

    historico_json = [json.loads(conversao) for conversao in historico]
    return historico_json

@app.get("/taxas")
def listar_moedas():
    chaves = r.keys("*")
    moedas = [chave for chave in chaves if chave != "historico"]

    if not moedas:
        return {"USD": 1.0, "BRL": 5.0, "ARS": 700.0}

    taxas = {}
    for moeda in moedas:
        valor = r.get(moeda)
        if valor is not None:
            taxas[moeda] = float(valor)
    return taxas


@app.delete("/taxas/{moeda}", status_code=status.HTTP_200_OK)
def deletar_taxa(moeda: str):
    if not r.exists(moeda.upper()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Moeda não encontrada.")
    r.delete(moeda.upper())
    return {"message": f"Taxa de {moeda.upper()} removida."}

# Configuração de CORS para permitir que o React converse com a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)