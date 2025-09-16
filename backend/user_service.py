import uuid
from datetime import datetime
from typing import Dict, List, Optional
from models import User, UserRole, RideRequest, RideStatus, NotificationData
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Serviço para gestão de usuários e ride requests"""
    
    def __init__(self):
        # Cache em memória para demonstração
        # Em produção, usar banco de dados real
        self.users: Dict[str, User] = {}
        self.ride_requests: Dict[str, RideRequest] = {}
        self.notifications: Dict[str, List[NotificationData]] = {}
        
        # Inicializar com dados de demonstração
        self._initialize_demo_data()
    
    def _initialize_demo_data(self):
        """Inicializa com usuários de demonstração"""
        demo_users = [
            User(
                id="DRV-001",
                name="João Silva",
                role=UserRole.DRIVER,
                contact="joao@email.com",
                created_at=datetime.utcnow()
            ),
            User(
                id="DRV-002", 
                name="Maria Santos",
                role=UserRole.DRIVER,
                contact="maria@email.com",
                created_at=datetime.utcnow()
            ),
            User(
                id="EMP-001",
                name="TransLog Empresa",
                role=UserRole.ENTERPRISE,
                contact="admin@translog.com",
                created_at=datetime.utcnow()
            ),
            User(
                id="ADM-001",
                name="Sistema Admin",
                role=UserRole.ADMIN,
                contact="admin@sentra.com",
                created_at=datetime.utcnow()
            )
        ]
        
        for user in demo_users:
            self.users[user.id] = user
            self.notifications[user.id] = []
            
        logger.info(f"Inicializado com {len(demo_users)} usuários de demonstração")
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Obtém um usuário pelo ID"""
        return self.users.get(user_id)
    
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Obtém todos os usuários de uma role específica"""
        return [user for user in self.users.values() if user.role == role and user.is_active]
    
    async def create_user(self, user_data: Dict) -> User:
        """Cria um novo usuário"""
        user_id = user_data.get("id") or f"{user_data['role'].upper()}-{uuid.uuid4().hex[:8]}"
        
        user = User(
            id=user_id,
            name=user_data["name"],
            role=UserRole(user_data["role"]),
            contact=user_data["contact"],
            created_at=datetime.utcnow()
        )
        
        self.users[user_id] = user
        self.notifications[user_id] = []
        
        logger.info(f"Usuário criado: {user_id} ({user.role})")
        return user
    
    async def create_ride_request(self, enterprise_id: str, driver_id: str, trip_data) -> RideRequest:
        """Cria uma nova solicitação de corrida"""
        # Validações
        enterprise = await self.get_user(enterprise_id)
        if not enterprise or enterprise.role != UserRole.ENTERPRISE:
            raise ValueError("Empresa não encontrada ou inválida")
        
        driver = await self.get_user(driver_id)
        if not driver or driver.role != UserRole.DRIVER:
            raise ValueError("Motorista não encontrado ou inválido")
        
        # Verifica se o driver já tem uma corrida pendente ou em andamento
        active_requests = [
            req for req in self.ride_requests.values() 
            if req.driver_id == driver_id and req.status in [RideStatus.PENDENTE, RideStatus.ACEITO, RideStatus.EM_ANDAMENTO]
        ]
        
        if active_requests:
            raise ValueError("Motorista já possui uma corrida ativa")
        
        # Cria a solicitação
        request_id = f"REQ-{uuid.uuid4().hex[:8]}"
        ride_request = RideRequest(
            id=request_id,
            enterprise_id=enterprise_id,
            driver_id=driver_id,
            trip_data=trip_data,
            status=RideStatus.PENDENTE,
            created_at=datetime.utcnow()
        )
        
        self.ride_requests[request_id] = ride_request
        
        # Criar notificação para o driver
        await self._create_notification(
            driver_id,
            "ride_request",
            "Nova Corrida Disponível",
            f"A empresa {enterprise.name} enviou uma solicitação de corrida.",
            {"ride_request_id": request_id, "enterprise_name": enterprise.name}
        )
        
        logger.info(f"Solicitação de corrida criada: {request_id} (Enterprise: {enterprise_id}, Driver: {driver_id})")
        return ride_request
    
    async def accept_ride_request(self, request_id: str, driver_id: str) -> RideRequest:
        """Driver aceita uma solicitação de corrida"""
        ride_request = self.ride_requests.get(request_id)
        if not ride_request:
            raise ValueError("Solicitação não encontrada")
        
        if ride_request.driver_id != driver_id:
            raise ValueError("Apenas o motorista designado pode aceitar esta corrida")
        
        if ride_request.status != RideStatus.PENDENTE:
            raise ValueError(f"Corrida não pode ser aceita. Status atual: {ride_request.status}")
        
        # Atualiza status
        ride_request.status = RideStatus.ACEITO
        ride_request.accepted_at = datetime.utcnow()
        
        # Notifica a empresa
        enterprise = await self.get_user(ride_request.enterprise_id)
        driver = await self.get_user(driver_id)
        
        await self._create_notification(
            ride_request.enterprise_id,
            "ride_accepted",
            "Corrida Aceita",
            f"O motorista {driver.name} aceitou a corrida {request_id}.",
            {"ride_request_id": request_id, "driver_name": driver.name}
        )
        
        logger.info(f"Corrida aceita: {request_id} por {driver_id}")
        return ride_request
    
    async def reject_ride_request(self, request_id: str, driver_id: str, reason: Optional[str] = None) -> RideRequest:
        """Driver rejeita uma solicitação de corrida"""
        ride_request = self.ride_requests.get(request_id)
        if not ride_request:
            raise ValueError("Solicitação não encontrada")
        
        if ride_request.driver_id != driver_id:
            raise ValueError("Apenas o motorista designado pode rejeitar esta corrida")
        
        if ride_request.status != RideStatus.PENDENTE:
            raise ValueError(f"Corrida não pode ser rejeitada. Status atual: {ride_request.status}")
        
        # Atualiza status
        ride_request.status = RideStatus.RECUSADO
        ride_request.rejected_at = datetime.utcnow()
        ride_request.rejection_reason = reason
        
        # Notifica a empresa
        enterprise = await self.get_user(ride_request.enterprise_id)
        driver = await self.get_user(driver_id)
        
        reason_text = f" Motivo: {reason}" if reason else ""
        await self._create_notification(
            ride_request.enterprise_id,
            "ride_rejected",
            "Corrida Rejeitada",
            f"O motorista {driver.name} rejeitou a corrida {request_id}.{reason_text}",
            {"ride_request_id": request_id, "driver_name": driver.name, "reason": reason}
        )
        
        logger.info(f"Corrida rejeitada: {request_id} por {driver_id}. Motivo: {reason}")
        return ride_request
    
    async def start_ride(self, request_id: str, enterprise_id: str) -> RideRequest:
        """Enterprise inicia uma corrida aceita"""
        ride_request = self.ride_requests.get(request_id)
        if not ride_request:
            raise ValueError("Solicitação não encontrada")
        
        if ride_request.enterprise_id != enterprise_id:
            raise ValueError("Apenas a empresa solicitante pode iniciar esta corrida")
        
        if ride_request.status != RideStatus.ACEITO:
            raise ValueError(f"Corrida não pode ser iniciada. Status atual: {ride_request.status}")
        
        # Atualiza status
        ride_request.status = RideStatus.EM_ANDAMENTO
        ride_request.started_at = datetime.utcnow()
        
        # Notifica o driver
        await self._create_notification(
            ride_request.driver_id,
            "ride_started",
            "Corrida Iniciada",
            f"A corrida {request_id} foi iniciada. Você pode começar o percurso.",
            {"ride_request_id": request_id}
        )
        
        logger.info(f"Corrida iniciada: {request_id}")
        return ride_request
    
    async def get_ride_requests_for_user(self, user_id: str, status: Optional[RideStatus] = None) -> List[RideRequest]:
        """Obtém solicitações de corrida para um usuário"""
        user = await self.get_user(user_id)
        if not user:
            return []
        
        requests = []
        for ride_request in self.ride_requests.values():
            # Driver vê apenas suas próprias solicitações
            if user.role == UserRole.DRIVER and ride_request.driver_id == user_id:
                requests.append(ride_request)
            # Enterprise vê apenas suas próprias solicitações
            elif user.role == UserRole.ENTERPRISE and ride_request.enterprise_id == user_id:
                requests.append(ride_request)
            # Admin vê todas
            elif user.role == UserRole.ADMIN:
                requests.append(ride_request)
        
        # Filtro por status se especificado
        if status:
            requests = [req for req in requests if req.status == status]
        
        # Ordena por data de criação (mais recentes primeiro)
        requests.sort(key=lambda x: x.created_at, reverse=True)
        return requests
    
    async def get_ride_request(self, request_id: str) -> Optional[RideRequest]:
        """Obtém uma solicitação específica"""
        return self.ride_requests.get(request_id)
    
    async def _create_notification(self, user_id: str, notification_type: str, title: str, message: str, data: Optional[Dict] = None):
        """Cria uma notificação para um usuário"""
        notification = NotificationData(
            id=f"NOTIF-{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            data=data or {}
        )
        
        if user_id not in self.notifications:
            self.notifications[user_id] = []
        
        self.notifications[user_id].append(notification)
        
        # Manter apenas as últimas 50 notificações por usuário
        if len(self.notifications[user_id]) > 50:
            self.notifications[user_id] = self.notifications[user_id][-50:]
    
    async def get_notifications(self, user_id: str, unread_only: bool = False) -> List[NotificationData]:
        """Obtém notificações de um usuário"""
        notifications = self.notifications.get(user_id, [])
        
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        # Ordena por data (mais recentes primeiro)
        notifications.sort(key=lambda x: x.created_at, reverse=True)
        return notifications
    
    async def mark_notification_read(self, user_id: str, notification_id: str):
        """Marca uma notificação como lida"""
        notifications = self.notifications.get(user_id, [])
        for notification in notifications:
            if notification.id == notification_id:
                notification.read = True
                break