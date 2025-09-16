from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    DRIVER = "driver"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"

class RideStatus(str, Enum):
    PENDENTE = "Pendente"
    ACEITO = "Aceito"
    RECUSADO = "Recusado"
    EM_ANDAMENTO = "EmAndamento"
    FINALIZADO = "Finalizado"
    CANCELADO = "Cancelado"

class User(BaseModel):
    """Modelo para usuários do sistema"""
    id: str = Field(..., description="ID único do usuário")
    name: str = Field(..., description="Nome completo")
    role: UserRole = Field(..., description="Role do usuário")
    contact: str = Field(..., description="Email ou telefone para contato")
    is_active: bool = Field(default=True, description="Status ativo do usuário")
    created_at: Optional[datetime] = Field(default=None, description="Data de criação")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "DRV-001",
                "name": "João Silva",
                "role": "driver",
                "contact": "joao@email.com",
                "is_active": True
            }
        }

class RideRequest(BaseModel):
    """Modelo para solicitações de corrida"""
    id: str = Field(..., description="ID único da solicitação")
    enterprise_id: str = Field(..., description="ID da empresa solicitante")
    driver_id: str = Field(..., description="ID do motorista alvo")
    trip_data: 'TripData' = Field(..., description="Dados da viagem")
    status: RideStatus = Field(default=RideStatus.PENDENTE, description="Status da solicitação")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Data de criação")
    accepted_at: Optional[datetime] = Field(None, description="Data de aceite")
    rejected_at: Optional[datetime] = Field(None, description="Data de rejeição")
    started_at: Optional[datetime] = Field(None, description="Data de início")
    finished_at: Optional[datetime] = Field(None, description="Data de finalização")
    rejection_reason: Optional[str] = Field(None, description="Motivo da rejeição")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "REQ-001",
                "enterprise_id": "EMP-001",
                "driver_id": "DRV-001",
                "status": "Pendente",
                "trip_data": {
                    "trip_id": "TRIP-001",
                    "driver": "DRV-001",
                    "route": ["Origin", "Waypoint", "Destination"]
                }
            }
        }

class TripData(BaseModel):
    """Modelo para dados de criação de viagem"""
    trip_id: str = Field(..., description="ID único da viagem")
    driver: str = Field(..., description="ID/Endereço do motorista")
    route: List[str] = Field(..., description="Lista de coordenadas da rota [saída, meio, chegada]")
    saida_checkpoint: Optional[str] = Field(None, description="Endereço autorizado para marcar saída")
    meio_checkpoint: Optional[str] = Field(None, description="Endereço autorizado para checkpoint intermediário")
    chegada_checkpoint: Optional[str] = Field(None, description="Endereço autorizado para chegada")
    origin_address: Optional[str] = Field(None, description="Endereço de origem")
    destination_address: Optional[str] = Field(None, description="Endereço de destino")
    estimated_duration: Optional[int] = Field(None, description="Duração estimada em minutos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trip_id": "TRIP-001",
                "driver": "DRV-001", 
                "route": ["lat1,lng1", "lat2,lng2", "lat3,lng3"],
                "origin_address": "Rio de Janeiro, RJ",
                "destination_address": "São Paulo, SP",
                "estimated_duration": 360
            }
        }

class ContractUpdate(BaseModel):
    """Modelo para atualizações de contrato"""
    trip_id: str = Field(..., description="ID da viagem")
    event: str = Field(..., description="Tipo do evento (checkpoint, delivery, etc)")
    status: str = Field(..., description="Status do evento")
    location: Optional[str] = Field(None, description="Localização atual")
    timestamp: Optional[datetime] = Field(None, description="Timestamp do evento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trip_id": "TRIP-001",
                "event": "checkpoint",
                "status": "ok",
                "location": "lat,lng",
                "timestamp": "2025-01-01T10:00:00Z"
            }
        }

class ContractResponse(BaseModel):
    """Modelo padrão de resposta da API"""
    success: bool = Field(..., description="Indica se a operação foi bem-sucedida")
    message: str = Field(..., description="Mensagem descritiva")
    data: Optional[Dict[str, Any]] = Field(None, description="Dados da resposta")
    error: Optional[str] = Field(None, description="Detalhes do erro, se houver")

class RideAcceptRequest(BaseModel):
    """Modelo para aceite de corrida"""
    driver_id: str = Field(..., description="ID do motorista que está aceitando")
    
class RideRejectRequest(BaseModel):
    """Modelo para rejeição de corrida"""
    driver_id: str = Field(..., description="ID do motorista que está rejeitando")
    reason: Optional[str] = Field(None, description="Motivo da rejeição")

class NotificationData(BaseModel):
    """Modelo para notificações"""
    id: str
    user_id: str
    type: str  # "ride_request", "ride_accepted", "ride_rejected"
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StellarConfig(BaseModel):
    """Configuração para Stellar Network"""
    network: str = Field(default="testnet", description="Rede Stellar (testnet/mainnet)")
    horizon_url: str = Field(..., description="URL do servidor Horizon")
    secret_key: str = Field(..., description="Chave secreta da conta")
    public_key: str = Field(..., description="Chave pública da conta")
    contract_id: Optional[str] = Field(None, description="ID do contrato inteligente")

class ContractState(BaseModel):
    """Estado atual de um contrato baseado no smart contract Soroban"""
    trip_id: str
    driver: str
    route: List[str]
    status: str  # Pendente, EmAndamento, PontoIntermediario, Finalizada
    saida_checkpoint: str
    meio_checkpoint: str
    chegada_checkpoint: str
    current_location: Optional[str] = None
    checkpoints: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime
    contract_address: str
    
class TransactionResult(BaseModel):
    """Resultado de uma transação Stellar"""
    transaction_hash: str
    success: bool
    ledger: Optional[int] = None
    fee_charged: Optional[str] = None
    result_xdr: Optional[str] = None

class CreateRideRequestBody(BaseModel):
    enterprise_id: str = Field(..., description="ID da empresa solicitante")
    driver_id: str = Field(..., description="ID do motorista alvo")
    trip_data: TripData = Field(..., description="Dados da viagem")
    
class StartRideRequest(BaseModel):
    enterprise_id: str

# Fix forward reference
RideRequest.model_rebuild()