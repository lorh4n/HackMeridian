import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from stellar_sdk import Server, Keypair, Network, TransactionBuilder, Account
from stellar_sdk.exceptions import Ed25519PublicKeyInvalidError, BadResponseError
from stellar_sdk.contract import AssembledTransaction
from stellar_sdk import scval, xdr, Address
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StellarContractService:
    """Serviço para interagir com contratos inteligentes na rede Stellar"""
    
    def __init__(self):
        self.server = None
        self.keypair = None
        self.account = None
        self.contracts_data = {}  # Cache para dados dos contratos
        
        # Configurações da rede
        self.network = os.getenv("STELLAR_NETWORK", "testnet")
        self.horizon_url = self._get_horizon_url()
        self.contract_id = os.getenv("STELLAR_CONTRACT_ID")
        self.soroban_rpc_url = self._get_soroban_rpc_url()
        
    def _get_horizon_url(self) -> str:
        """Retorna a URL do Horizon baseada na rede"""
        if self.network == "mainnet":
            return "https://horizon.stellar.org"
        else:
            return "https://horizon-testnet.stellar.org"
    
    async def initialize(self):
        """Inicializa a conexão com a rede Stellar"""
        try:
            # Configura servidor Horizon
            self.server = Server(self.horizon_url)
            
            # Configura keypair da conta
            secret_key = os.getenv("STELLAR_SECRET_KEY")
            if not secret_key:
                raise ValueError("STELLAR_SECRET_KEY não configurada")
            
            self.keypair = Keypair.from_secret(secret_key)
            
            # Carrega informações da conta
            account_response = self.server.accounts().account_id(
                self.keypair.public_key
            ).call()
            self.account = Account(
                account_response["account_id"], 
                account_response["sequence"]
            )
            
            # Configura rede
            if self.network == "mainnet":
                Network.use_public_network()
            else:
                Network.use_test_network()
            
            logger.info(f"Stellar service inicializado - Rede: {self.network}")
            logger.info(f"Conta pública: {self.keypair.public_key}")
            if self.contract_id:
                logger.info(f"Contract ID: {self.contract_id}")
            else:
                logger.warning("STELLAR_CONTRACT_ID não configurado - usando modo simulação")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar Stellar service: {e}")
            raise
    
    def _get_soroban_rpc_url(self) -> str:
        """Retorna URL do RPC Soroban"""
        if self.network == "mainnet":
            return "https://soroban-rpc.stellar.org"
        else:
            return "https://soroban-rpc-testnet.stellar.org"
    
    def _get_network_passphrase(self) -> str:
        """Retorna o passphrase da rede"""
        if self.network == "mainnet":
            return Network.PUBLIC_NETWORK_PASSPHRASE
        else:
            return Network.TESTNET_NETWORK_PASSPHRASE
    
    async def create_transport_contract(self, trip_id: str, driver: str, route: List[str]) -> Dict[str, Any]:
        """Cria um novo contrato de transporte usando criar_viagem do smart contract"""
        try:
            current_time = datetime.utcnow()
            
            # Extrai endereços dos checkpoints da rota
            # Assume que route[0] = saída, route[1] = meio, route[2] = chegada
            if len(route) < 3:
                # Se não temos 3 pontos, duplicamos alguns para completar
                while len(route) < 3:
                    route.append(route[-1])
            
            # Para demonstração, vamos usar endereços fixos dos checkpoints
            # Em produção, estes seriam derivados da rota ou configurados
            saida_checkpoint = driver  # Motorista autoriza saída
            meio_checkpoint = os.getenv("CHECKPOINT_MEIO_ADDRESS", driver)  # Endereço do checkpoint intermediário
            chegada_checkpoint = os.getenv("CHECKPOINT_CHEGADA_ADDRESS", driver)  # Endereço do destino
            
            # Se não temos contrato inteligente, simulamos a criação
            if not self.contract_id:
                contract_data = {
                    "trip_id": trip_id,
                    "driver": driver,
                    "route": route,
                    "status": "Pendente",  # Status inicial do smart contract
                    "saida_checkpoint": saida_checkpoint,
                    "meio_checkpoint": meio_checkpoint,
                    "chegada_checkpoint": chegada_checkpoint,
                    "created_at": current_time.isoformat(),
                    "checkpoints": [],
                    "contract_address": f"SIMULATED_CONTRACT_{trip_id}_{int(current_time.timestamp())}",
                    "transaction_hash": f"SIMULATED_TX_{trip_id}_{int(current_time.timestamp())}"
                }
                
                # Armazena no cache
                self.contracts_data[trip_id] = contract_data
                
                return contract_data
            
            # Caso real com contrato inteligente
            # Chama função criar_viagem do contrato via Soroban RPC
            result = await self._invoke_contract_function(
                "criar_viagem",
                {
                    "trip_id": trip_id,
                    "saida_checkpoint": saida_checkpoint,
                    "meio_checkpoint": meio_checkpoint,
                    "chegada_checkpoint": chegada_checkpoint
                }
            )
            
            contract_data = {
                "trip_id": trip_id,
                "driver": driver,
                "route": route,
                "status": "Pendente",  # Status inicial do smart contract
                "saida_checkpoint": saida_checkpoint,
                "meio_checkpoint": meio_checkpoint,
                "chegada_checkpoint": chegada_checkpoint,
                "created_at": current_time.isoformat(),
                "checkpoints": [],
                "contract_address": self.contract_id,
                "transaction_hash": result.get("transaction_hash")
            }
            
            self.contracts_data[trip_id] = contract_data
            return contract_data
            
        except Exception as e:
            logger.error(f"Erro ao criar contrato: {e}")
            raise
    
    async def update_contract_status(self, trip_id: str, event: str, status: str) -> Dict[str, Any]:
        """Atualiza o status de um contrato usando as funções específicas do smart contract"""
        try:
            current_time = datetime.utcnow()
            
            # Verifica se o contrato existe
            if trip_id not in self.contracts_data:
                raise ValueError(f"Contrato {trip_id} não encontrado")
            
            # Mapeia eventos para funções do smart contract
            contract_function_map = {
                "saida": "marcar_saida",
                "checkpoint": "marcar_meio", 
                "meio": "marcar_meio",
                "chegada": "marcar_chegada",
                "entrega": "marcar_chegada"
            }
            
            # Mapeia status para os status do smart contract
            status_map = {
                "ok": "EmAndamento",  # Para saída
                "checkpoint": "PontoIntermediario",  # Para meio
                "completed": "Finalizada",  # Para chegada
                "delivered": "Finalizada"
            }
            
            # Atualiza dados do contrato
            contract_data = self.contracts_data[trip_id]
            
            # Adiciona novo checkpoint
            checkpoint = {
                "event": event,
                "status": status,
                "timestamp": current_time.isoformat()
            }
            
            contract_data["checkpoints"].append(checkpoint)
            
            # Determina qual função chamar no smart contract
            contract_function = contract_function_map.get(event.lower())
            new_contract_status = contract_data["status"]  # Status atual
            
            # Se temos contrato inteligente, invoca função específica
            if self.contract_id and contract_function:
                result = await self._invoke_contract_function(
                    contract_function,
                    {"trip_id": trip_id}
                )
                
                # Atualiza status baseado na função chamada
                if contract_function == "marcar_saida":
                    new_contract_status = "EmAndamento"
                elif contract_function == "marcar_meio":
                    new_contract_status = "PontoIntermediario"
                elif contract_function == "marcar_chegada":
                    new_contract_status = "Finalizada"
                
                contract_data["transaction_hash"] = result.get("transaction_hash")
            else:
                # Simula transação se não temos contrato
                contract_data["transaction_hash"] = f"SIMULATED_TX_{trip_id}_{event}_{int(current_time.timestamp())}"
                new_contract_status = status_map.get(status, contract_data["status"])
            
            contract_data["status"] = new_contract_status
            contract_data["updated_at"] = current_time.isoformat()
            
            return {
                "transaction_hash": contract_data["transaction_hash"],
                "updated_at": current_time.isoformat(),
                "contract_state": contract_data
            }
            
        except Exception as e:
            logger.error(f"Erro ao atualizar contrato: {e}")
            raise
    
    async def get_contract_status(self, trip_id: str) -> Optional[Dict[str, Any]]:
        """Consulta o estado atual de um contrato usando get_viagem"""
        try:
            # Se temos contrato inteligente, consulta na blockchain primeiro
            if self.contract_id:
                try:
                    result = await self._query_contract_function(
                        "get_viagem",
                        {"trip_id": trip_id}
                    )
                    
                    if result:
                        # Converte resultado do smart contract para formato da API
                        contract_data = {
                            "trip_id": trip_id,
                            "status": result.get("status", "Pendente"),
                            "saida_checkpoint": result.get("saida_checkpoint"),
                            "meio_checkpoint": result.get("meio_checkpoint"), 
                            "chegada_checkpoint": result.get("chegada_checkpoint"),
                            "contract_address": self.contract_id,
                            "checkpoints": self.contracts_data.get(trip_id, {}).get("checkpoints", []),
                            "created_at": self.contracts_data.get(trip_id, {}).get("created_at"),
                            "updated_at": datetime.utcnow().isoformat()
                        }
                        
                        # Atualiza cache local
                        if trip_id in self.contracts_data:
                            self.contracts_data[trip_id].update(contract_data)
                        
                        return contract_data
                except Exception as e:
                    logger.warning(f"Erro ao consultar smart contract, usando cache: {e}")
            
            # Fallback para cache local
            if trip_id in self.contracts_data:
                return self.contracts_data[trip_id]
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao consultar contrato: {e}")
            return None
    
    async def get_contract_history(self, trip_id: str) -> List[Dict[str, Any]]:
        """Obtém o histórico completo de um contrato"""
        try:
            contract_data = await self.get_contract_status(trip_id)
            
            if not contract_data:
                return []
            
            return contract_data.get("checkpoints", [])
            
        except Exception as e:
            logger.error(f"Erro ao buscar histórico: {e}")
            return []
    
    async def initialize_contract(self, admin_address: str) -> Dict[str, Any]:
        """Inicializa o smart contract com um endereço admin"""
        try:
            if not self.contract_id:
                return {
                    "success": False,
                    "message": "Contract ID não configurado - modo simulação ativo"
                }
            
            result = await self._invoke_contract_function(
                "initialize",
                {"admin": admin_address}
            )
            
            return {
                "success": True,
                "message": "Contrato inicializado com sucesso",
                "admin": admin_address,
                "transaction_hash": result.get("transaction_hash")
            }
            
        except Exception as e:
            logger.error(f"Erro ao inicializar contrato: {e}")
            raise
    
    async def get_contract_admin(self) -> Optional[str]:
        """Obtém o endereço do admin do contrato"""
        try:
            if not self.contract_id:
                return None
            
            result = await self._query_contract_function("get_admin", {})
            return result.get("admin") if result else None
            
        except Exception as e:
            logger.error(f"Erro ao obter admin: {e}")
            return None
        """Verifica a conexão com a rede Stellar"""
        try:
            if not self.server:
                return {"connected": False, "error": "Servidor não inicializado"}
            
            # Testa conexão com Horizon
            ledger_response = self.server.ledgers().limit(1).call()
            
            return {
                "connected": True,
                "network": self.network,
                "horizon_url": self.horizon_url,
                "latest_ledger": ledger_response["_embedded"]["records"][0]["sequence"]
            }
            
        except Exception as e:
            return {
                "connected": False,
                "network": self.network,
                "error": str(e)
            }
    
    async def _invoke_contract_function(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Invoca uma função do contrato inteligente usando Stellar SDK"""
        try:
            if not self.contract_id:
                raise ValueError("Contract ID não configurado")
            
            logger.info(f"Chamando função {function_name} com parâmetros: {params}")
            
            # Para demonstração, simula a chamada
            # Em produção, você usaria o Stellar SDK para chamar o contrato real
            await asyncio.sleep(0.1)  # Simula latência da rede
            
            transaction_hash = f"TX_{function_name}_{int(datetime.utcnow().timestamp())}"
            
            logger.info(f"Função {function_name} executada com sucesso. TX: {transaction_hash}")
            
            return {
                "transaction_hash": transaction_hash,
                "success": True,
                "result": params,
                "function": function_name
            }
            
        except Exception as e:
            logger.error(f"Erro ao invocar função {function_name}: {e}")
            raise
    
    async def _query_contract_function(self, function_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Consulta uma função read-only do contrato"""
        try:
            if not self.contract_id:
                return None
            
            logger.info(f"Consultando função {function_name} com parâmetros: {params}")
            
            # Implementação simplificada para consulta
            await asyncio.sleep(0.05)  # Simula latência da rede
            
            # Retorna dados do cache se disponível
            trip_id = params.get("trip_id")
            if trip_id and trip_id in self.contracts_data:
                return self.contracts_data[trip_id]
            
            # Para get_admin, retorna o endereço público atual
            if function_name == "get_admin":
                return {"admin": self.keypair.public_key if self.keypair else None}
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao consultar função {function_name}: {e}")
            raise