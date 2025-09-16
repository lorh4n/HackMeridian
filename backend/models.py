from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class TripData(BaseModel):
    """Modelo para dados de criação de viagem"""
    trip_id: str = Field(..., description="ID único da viagem")
    driver: str = Field(..., description="ID/Endereço do motorista")
    route: List[str] = Field(..., description="Lista de coordenadas da rota [saída, meio, chegada]")
    saida_checkpoint: Optional[str] = Field(None, description="Endereço autorizado para marcar saída")
    meio_checkpoint: Optional[str] = Field(None, description="Endereço autorizado para checkpoint intermediário")
    chegada_checkpoint: Optional[str] = Field(None, description="Endereço autorizado para chegada")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trip_id": "TRIP-001",
                "driver": "GBXYZ...ABC", 
                "route": ["lat1,lng1", "lat2,lng2", "lat3,lng3"],
                "saida_checkpoint": "GBXYZ...ABC",
                "meio_checkpoint": "GBABC...XYZ", 
                "chegada_checkpoint": "GBDEF...123"
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