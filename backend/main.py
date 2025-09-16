from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv
import uvicorn
from models import (
    TripData, ContractUpdate, ContractResponse, User, UserRole, 
    RideRequest, RideAcceptRequest, RideRejectRequest, RideStatus, CreateRideRequestBody,  StartRideRequest
)
from stellar_service import StellarContractService
from user_service import UserService
from typing import Optional, List

load_dotenv()

app = FastAPI(
    title="Stellar Transport Contracts API",
    description="API para gestão de contratos inteligentes de transporte na blockchain Stellar",
    version="2.0.0"
)

# Configuração CORS para o frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Inicializa os serviços
stellar_service = StellarContractService()
user_service = UserService()

# =================== ROTAS DE INTERFACE ===================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Tela inicial - seleção entre Driver e Enterprise Mode"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/driver", response_class=HTMLResponse)
async def driver_interface(request: Request):
    """Interface do motorista"""
    return templates.TemplateResponse("driver.html", {"request": request})

@app.get("/enterprise", response_class=HTMLResponse)
async def enterprise_interface(request: Request):
    """Interface da empresa"""
    return templates.TemplateResponse("enterprise.html", {"request": request})

# =================== ROTAS DE USUÁRIOS ===================

@app.get("/api/users")
async def get_users(role: Optional[UserRole] = None):
    """Lista usuários, opcionalmente filtrados por role"""
    try:
        if role:
            users = await user_service.get_users_by_role(role)
        else:
            users = list(user_service.users.values())
        
        return ContractResponse(
            success=True,
            message="Usuários recuperados com sucesso",
            data={"users": [user.dict() for user in users]}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar usuários: {str(e)}"
        )

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """Obtém informações de um usuário específico"""
    try:
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuário não encontrado"
            )
        
        return ContractResponse(
            success=True,
            message="Usuário encontrado",
            data={"user": user.dict()}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar usuário: {str(e)}"
        )

@app.post("/api/users")
async def create_user(user_data: dict):
    """Cria um novo usuário"""
    try:
        user = await user_service.create_user(user_data)
        
        return ContractResponse(
            success=True,
            message="Usuário criado com sucesso",
            data={"user": user.dict()}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar usuário: {str(e)}"
        )

# =================== ROTAS DE RIDE REQUESTS ===================

@app.get("/api/ride-requests")
async def get_ride_requests(user_id: str, status: Optional[RideStatus] = None):
    """Lista ride requests para um usuário"""
    try:
        requests = await user_service.get_ride_requests_for_user(user_id, status)
        
        return ContractResponse(
            success=True,
            message="Solicitações recuperadas",
            data={"ride_requests": [req.dict() for req in requests]}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar solicitações: {str(e)}"
        )

@app.post("/api/ride-requests")
async def create_ride_request(request_body: CreateRideRequestBody):
    """Empresa cria uma solicitação de corrida"""
    try:
        print("=========== TENTATIVO DE CRIAR ROTA ==============")
        print(f"Request body recebido: {request_body}")
        print(f"Enterprise ID: {request_body.enterprise_id}")
        print(f"Driver ID: {request_body.driver_id}")
        print(f"Trip Data: {request_body.trip_data}")
        
        ride_request = await user_service.create_ride_request(
            enterprise_id=request_body.enterprise_id,
            driver_id=request_body.driver_id,
            trip_data=request_body.trip_data
        )
        
        return ContractResponse(
            success=True,
            message="Solicitação de corrida criada",
            data={"ride_request": ride_request.dict()}
        )
    except ValueError as e:
        print("=========== ERRO DE VALIDAÇÃO ==============")
        print(f"Erro: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        print("=========== ERRO GERAL ==============")
        print(f"Erro: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar solicitação: {str(e)}"
        )

@app.get("/api/ride-requests/{request_id}")
async def get_ride_request(request_id: str):
    """Obtém detalhes de uma solicitação específica"""
    try:
        ride_request = await user_service.get_ride_request(request_id)
        if not ride_request:
            raise HTTPException(
                status_code=404,
                detail="Solicitação não encontrada"
            )
        
        return ContractResponse(
            success=True,
            message="Solicitação encontrada",
            data={"ride_request": ride_request.dict()}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar solicitação: {str(e)}"
        )

@app.post("/api/ride-requests/{request_id}/accept")
async def accept_ride_request(request_id: str, accept_data: RideAcceptRequest):
    """Driver aceita uma solicitação de corrida"""
    try:
        ride_request = await user_service.accept_ride_request(
            request_id=request_id,
            driver_id=accept_data.driver_id
        )
        
        return ContractResponse(
            success=True,
            message="Corrida aceita com sucesso",
            data={"ride_request": ride_request.dict()}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao aceitar corrida: {str(e)}"
        )

@app.post("/api/ride-requests/{request_id}/reject")
async def reject_ride_request(request_id: str, reject_data: RideRejectRequest):
    """Driver rejeita uma solicitação de corrida"""
    try:
        ride_request = await user_service.reject_ride_request(
            request_id=request_id,
            driver_id=reject_data.driver_id,
            reason=reject_data.reason
        )
        
        return ContractResponse(
            success=True,
            message="Corrida rejeitada",
            data={"ride_request": ride_request.dict()}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao rejeitar corrida: {str(e)}"
        )

@app.post("/api/ride-requests/{request_id}/start")
async def start_ride(request_id: str, start_data: StartRideRequest):
    """Enterprise inicia uma corrida aceita"""
    try:
        ride_request = await user_service.start_ride(
            request_id=request_id,
            enterprise_id=start_data.enterprise_id  # Mudança aqui
        )
        
        # Também cria o contrato na blockchain quando a corrida inicia
        if ride_request.status == RideStatus.EM_ANDAMENTO:
            contract_result = await stellar_service.create_transport_contract(
                trip_id=ride_request.trip_data.trip_id,
                driver=ride_request.driver_id,
                route=ride_request.trip_data.route
            )
            
            return ContractResponse(
                success=True,
                message="Corrida iniciada e contrato criado na blockchain",
                data={
                    "ride_request": ride_request.dict(),
                    "contract": contract_result
                }
            )
        
        return ContractResponse(
            success=True,
            message="Corrida iniciada",
            data={"ride_request": ride_request.dict()}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao iniciar corrida: {str(e)}"
        )

# =================== ROTAS DE NOTIFICAÇÕES ===================

@app.get("/api/notifications/{user_id}")
async def get_notifications(user_id: str, unread_only: bool = False):
    """Obtém notificações de um usuário"""
    try:
        notifications = await user_service.get_notifications(user_id, unread_only)
        
        return ContractResponse(
            success=True,
            message="Notificações recuperadas",
            data={"notifications": [notif.dict() for notif in notifications]}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar notificações: {str(e)}"
        )

@app.post("/api/notifications/{user_id}/{notification_id}/read")
async def mark_notification_read(user_id: str, notification_id: str):
    """Marca uma notificação como lida"""
    try:
        await user_service.mark_notification_read(user_id, notification_id)
        
        return ContractResponse(
            success=True,
            message="Notificação marcada como lida",
            data={}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao marcar notificação: {str(e)}"
        )

# =================== ROTAS ORIGINAIS DE CONTRATOS (COMPATIBILIDADE) ===================

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

@app.get("/contract/{trip_id}/history")
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
            "stellar_connected": stellar_status.get("connected", False),
            "users_count": len(user_service.users),
            "ride_requests_count": len(user_service.ride_requests)
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