from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import uvicorn
from models import TripData, ContractUpdate, ContractResponse
from stellar_service import StellarContractService

load_dotenv()

app = FastAPI(
    title="Stellar Transport Contracts API",
    description="API para gestão de contratos inteligentes de transporte na blockchain Stellar",
    version="1.0.0"
)

# Configuração CORS para o frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa o serviço Stellar
stellar_service = StellarContractService()

# @app.on_startup
# async def startup():
#     """Inicializa conexão com Stellar na inicialização"""
#     await stellar_service.initialize()

@app.get("/")
async def root():
    return {"message": "Stellar Transport Contracts API", "status": "running"}

@app.post("/contract/create")
async def create_contract(trip_data: TripData):
    """
    Cria um novo contrato de transporte na blockchain Stellar
    """
    try:
        result = await stellar_service.create_transport_contract(
            trip_id=trip_data.trip_id,
            driver=trip_data.driver,
            route=trip_data.route
        )
        
        return ContractResponse(
            success=True,
            message="Contrato criado com sucesso",
            data={
                "trip_id": trip_data.trip_id,
                "contract_address": result.get("contract_address"),
                "transaction_hash": result.get("transaction_hash"),
                "status": "created",
                "driver": trip_data.driver,
                "route": trip_data.route,
                "created_at": result.get("created_at")
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao criar contrato: {str(e)}"
        )

@app.post("/contract/manage")
async def manage_contract(update: ContractUpdate):
    """
    Atualiza o status de um contrato existente
    """
    try:
        result = await stellar_service.update_contract_status(
            trip_id=update.trip_id,
            event=update.event,
            status=update.status
        )
        
        return ContractResponse(
            success=True,
            message=f"Contrato atualizado - {update.event}",
            data={
                "trip_id": update.trip_id,
                "event": update.event,
                "status": update.status,
                "transaction_hash": result.get("transaction_hash"),
                "updated_at": result.get("updated_at"),
                "contract_state": result.get("contract_state")
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar contrato: {str(e)}"
        )

@app.get("/contract/{trip_id}")
async def view_contract(trip_id: str):
    """
    Consulta o estado atual de um contrato
    """
    try:
        contract_data = await stellar_service.get_contract_status(trip_id)
        
        if not contract_data:
            raise HTTPException(
                status_code=404, 
                detail="Contrato não encontrado"
            )
        
        return ContractResponse(
            success=True,
            message="Dados do contrato recuperados",
            data=contract_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar contrato: {str(e)}"
        )

@app.post("/contract/initialize")
async def initialize_contract():
    """
    Inicializa o smart contract com o admin atual
    """
    try:
        admin_address = stellar_service.keypair.public_key if stellar_service.keypair else None
        
        if not admin_address:
            raise HTTPException(
                status_code=400,
                detail="Endereço admin não disponível"
            )
        
        result = await stellar_service.initialize_contract(admin_address)
        
        return ContractResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            data=result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao inicializar contrato: {str(e)}"
        )

@app.get("/contract/admin")
async def get_contract_admin():
    """
    Obtém informações do admin do contrato
    """
    try:
        admin_address = await stellar_service.get_contract_admin()
        
        return ContractResponse(
            success=True,
            message="Informações do admin",
            data={
                "admin_address": admin_address,
                "current_keypair": stellar_service.keypair.public_key if stellar_service.keypair else None,
                "is_admin": admin_address == stellar_service.keypair.public_key if stellar_service.keypair and admin_address else False
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter admin: {str(e)}"
        )

@app.post("/contract/{trip_id}/saida")
async def marcar_saida(trip_id: str):
    """Marca a saída de uma viagem"""
    try:
        result = await stellar_service.update_contract_status(trip_id, "saida", "ok")
        
        return ContractResponse(
            success=True,
            message="Saída marcada com sucesso",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao marcar saída: {str(e)}"
        )

@app.post("/contract/{trip_id}/meio")
async def marcar_meio(trip_id: str):
    """Marca chegada ao checkpoint intermediário"""
    try:
        result = await stellar_service.update_contract_status(trip_id, "meio", "checkpoint")
        
        return ContractResponse(
            success=True,
            message="Checkpoint intermediário marcado",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao marcar checkpoint: {str(e)}"
        )

@app.post("/contract/{trip_id}/chegada")
async def marcar_chegada(trip_id: str):
    """Marca a chegada final da viagem"""
    try:
        result = await stellar_service.update_contract_status(trip_id, "chegada", "completed")
        
        return ContractResponse(
            success=True,
            message="Chegada marcada - viagem finalizada",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao marcar chegada: {str(e)}"
        )
async def get_contract_history(trip_id: str):
    """
    Obtém o histórico de eventos de um contrato
    """
    try:
        history = await stellar_service.get_contract_history(trip_id)
        
        return ContractResponse(
            success=True,
            message="Histórico do contrato",
            data={
                "trip_id": trip_id,
                "history": history
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar histórico: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Verifica a saúde da API e conexão com Stellar"""
    try:
        stellar_status = await stellar_service.check_connection()
        return {
            "status": "healthy",
            "stellar_network": stellar_status.get("network"),
            "stellar_connected": stellar_status.get("connected", False)
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development"
    )