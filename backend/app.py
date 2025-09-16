from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv

from stellar_sdk import Keypair, TransactionBuilder, Account, scval
from stellar_sdk.soroban_server import SorobanServer
from stellar_sdk import Account, MuxedAccount
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

RPC_URL = os.environ["RPC_URL"]
NETWORK_PASSPHRASE = os.environ["NETWORK_PASSPHRASE"]
CONTRACT_ID = os.environ["CONTRACT_ID"]

ADMIN_SECRET   = os.environ.get("ADMIN_SECRET")
SAIDA_SECRET   = os.environ.get("SAIDA_SECRET")
MEIO_SECRET    = os.environ.get("MEIO_SECRET")
CHEGADA_SECRET = os.environ.get("CHEGADA_SECRET")

server = SorobanServer(RPC_URL)
app = FastAPI(title="Meridian Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # em produção, restrinja
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Utils ---------
# --- SUBSTITUA seu _load_account por este ---
def _to_address(aid):
    return aid.address if hasattr(aid, "address") else str(aid)

def _load_account(account_id: str) -> Account:
    acc = server.load_account(account_id)

    # pegar sequence (pode estar no topo ou em .account)
    seq = getattr(acc, "sequence", None)
    if seq is None and hasattr(acc, "account"):
        seq = getattr(acc.account, "sequence", None)
    if seq is None:
        raise HTTPException(500, f"load_account sem sequence: {type(acc)} attrs={dir(acc)}")

    # pegar o account_id (string G... ou MuxedAccount)
    aid = getattr(acc, "account_id", None)
    if aid is None and hasattr(acc, "account"):
        aid = getattr(acc.account, "account_id", None)
    if aid is None and hasattr(acc, "id"):
        aid = acc.id

    # normalizar para MuxedAccount
    if isinstance(aid, MuxedAccount):
        mux = aid
    else:
        mux = MuxedAccount.from_account(_to_address(aid))

    # constrói o Account do SDK (assinatura correta)
    return Account(account=mux, sequence=int(seq))



def call_contract(source_kp: Keypair, func: str, args_scvals: List):
    # 1) montar tx base
    source_account = _load_account(source_kp.public_key)
    tx_base = (
        TransactionBuilder(
            source_account=source_account,
            network_passphrase=NETWORK_PASSPHRASE,
            base_fee=100  # qualquer valor; simulate ajusta as taxas/recurso
        )
        .append_invoke_contract_function_op(
            contract_id=CONTRACT_ID,
            function_name=func,
            parameters=args_scvals
        )
        .set_timeout(60)
        .build()
    )

    # 2) simulate -> aplica soroban_data e min_resource_fee
    sim = server.simulate_transaction(tx_base)

    # ------ tratamento robusto de erros de simulação ------
    err = getattr(sim, "error", None)
    if err:
        # pode ser string, objeto com .message, ou dict
        if isinstance(err, str):
            raise HTTPException(400, f"simulate error: {err}")
        msg = getattr(err, "message", None)
        raise HTTPException(400, f"simulate error: {msg or repr(err)}")

    # alguns SDKs colocam erro dentro do primeiro result
    if getattr(sim, "results", None):
        r0 = sim.results[0]
        r0_err = getattr(r0, "error", None)
        if r0_err:
            raise HTTPException(400, f"simulate result error: {r0_err}")

    # ------------------------------------------------------
    tx = server.prepare_transaction(tx_base, sim)

    # 3) assinar + enviar + poll
    tx.sign(source_kp)
    sent = server.send_transaction(tx)
    res = server.poll_transaction(sent.hash)
    if res.status != "SUCCESS":
        raise HTTPException(400, f"tx failed: {res.status}")
    return {
        "hash": res.transaction_hash,
        "status": res.status,
        "result_xdr": res.result_xdr,
        "events": res.events or []
    }

# --------- Schemas ---------
class CreateTripIn(BaseModel):
    trip_id: str
    saida_address: str
    meio_address: str
    chegada_address: str

class TripIdIn(BaseModel):
    trip_id: str

# --------- Rotas ----------
@app.get("/get_admin")
def get_admin():
    from stellar_sdk import scval
    if not ADMIN_SECRET:
        raise HTTPException(400, "ADMIN_SECRET não configurado")
    admin = Keypair.from_secret(ADMIN_SECRET)
    return call_contract(admin, "get_admin", [])

@app.get("/health")
def health():
    return {"rpc": RPC_URL, "passphrase": NETWORK_PASSPHRASE, "contract": CONTRACT_ID}

@app.post("/initialize")
def initialize():
    if not ADMIN_SECRET:
        raise HTTPException(400, "ADMIN_SECRET não configurado")
    admin = Keypair.from_secret(ADMIN_SECRET)
    return call_contract(admin, "initialize", [scval.to_address(admin.public_key)])

@app.post("/criar_viagem")
def criar_viagem(body: CreateTripIn):
    if not ADMIN_SECRET:
        raise HTTPException(400, "ADMIN_SECRET não configurado")
    admin = Keypair.from_secret(ADMIN_SECRET)
    args = [
        scval.to_string(body.trip_id),
        scval.to_address(body.saida_address),
        scval.to_address(body.meio_address),
        scval.to_address(body.chegada_address),
    ]
    return call_contract(admin, "criar_viagem", args)

@app.post("/marcar_saida")
def marcar_saida(body: TripIdIn):
    if not SAIDA_SECRET:
        raise HTTPException(400, "SAIDA_SECRET não configurado")
    kp = Keypair.from_secret(SAIDA_SECRET)
    return call_contract(kp, "marcar_saida", [scval.to_string(body.trip_id)])

@app.post("/marcar_meio")
def marcar_meio(body: TripIdIn):
    if not MEIO_SECRET:
        raise HTTPException(400, "MEIO_SECRET não configurado")
    kp = Keypair.from_secret(MEIO_SECRET)
    return call_contract(kp, "marcar_meio", [scval.to_string(body.trip_id)])

@app.post("/marcar_chegada")
def marcar_chegada(body: TripIdIn):
    if not CHEGADA_SECRET:
        raise HTTPException(400, "CHEGADA_SECRET não configurado")
    kp = Keypair.from_secret(CHEGADA_SECRET)
    return call_contract(kp, "marcar_chegada", [scval.to_string(body.trip_id)])

@app.get("/get_viagem")
def get_viagem(trip_id: str):
    if not ADMIN_SECRET:
        raise HTTPException(400, "ADMIN_SECRET não configurado")
    admin = Keypair.from_secret(ADMIN_SECRET)
    return call_contract(admin, "get_viagem", [scval.to_string(trip_id)])
