# SENTRA Transport Platform v2.0

Sistema descentralizado de transporte com contratos inteligentes na blockchain Stellar, agora com suporte completo a múltiplos usuários e fluxo Enterprise/Driver.

## 🚀 Novas Funcionalidades

### ✨ Sistema Multi-Usuário
- **Driver Mode**: Interface para motoristas aceitarem/rejeitarem corridas
- **Enterprise Mode**: Painel para empresas criarem e gerenciarem corridas
- **Sistema de Notificações**: Comunicação em tempo real entre partes
- **Gestão de Permissões**: Controle de acesso baseado em roles

### 🔄 Fluxo Completo de Corridas
1. **Enterprise** cria solicitação de corrida para **Driver específico**
2. **Driver** recebe notificação e pode **aceitar** ou **rejeitar**
3. Se aceito, **Enterprise** pode **iniciar a corrida** (cria contrato Stellar)
4. Sistema monitora progresso via checkpoints na blockchain

## 📋 Pré-requisitos

- Python 3.8+
- FastAPI
- Stellar SDK Python
- Jinja2 para templates
- Variáveis de ambiente configuradas (.env)

## 🛠️ Instalação

```bash
# Clonar repositório
git clone <repo-url>
cd sentra-transport

# Instalar dependências
pip install fastapi uvicorn stellar-sdk python-dotenv jinja2

# Criar pastas necessárias
mkdir -p templates static/css static/js

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações Stellar
```

## ⚙️ Configuração

### Arquivo .env
```bash
# Stellar Network
STELLAR_NETWORK=testnet
STELLAR_SECRET_KEY=your_secret_key
STELLAR_PUBLIC_KEY=your_public_key
STELLAR_CONTRACT_ID=your_contract_id

# API
PORT=3000
ENVIRONMENT=development
```

### Estrutura de Pastas
```
sentra-transport/
├── main.py                 # API principal
├── models.py              # Modelos de dados
├── user_service.py        # Serviço de usuários
├── stellar_service.py     # Serviço Stellar
├── templates/
│   ├── index.html         # Tela inicial
│   ├── driver.html        # Interface motorista
│   └── enterprise.html    # Interface empresa
├── static/
│   ├── css/
│   └── js/
└── README.md
```

## 🚀 Executar

```bash
# Desenvolvimento
python main.py

# Ou usando uvicorn diretamente
uvicorn main:app --host 0.0.0.0 --port 3000 --reload

# Acessar: http://localhost:3000
```

## 📱 Interfaces

### 🏠 Tela Inicial (`/`)
- Seleção entre **Driver Mode** e **Enterprise Mode**
- Design moderno com glassmorphism
- Animações e feedback visual

### 🚗 Driver Mode (`/driver`)
- Seleção de motorista (usuários demo inclusos)
- Lista de corridas pendentes/aceitas/em andamento
- Sistema de notificações em tempo real
- Ações: Aceitar, Rejeitar corridas
- Polling automático para atualizações

### 🏢 Enterprise Mode (`/enterprise`)
- Seleção de empresa
- Criação de novas corridas com formulário completo
- Seleção de motorista alvo
- Gestão de corridas: Iniciar, Monitorar, Cancelar
- Dashboard com métricas e status

## 🔗 API Endpoints

### Usuários
- `GET /api/users` - Lista usuários (filtro por role)
- `GET /api/users/{user_id}` - Detalhes do usuário
- `POST /api/users` - Criar usuário

### Solicitações de Corrida
- `GET /api/ride-requests?user_id=X` - Lista corridas do usuário
- `POST /api/ride-requests` - Criar nova corrida
- `GET /api/ride-requests/{id}` - Detalhes da corrida
- `POST /api/ride-requests/{id}/accept` - Driver aceita
- `POST /api/ride-requests/{id}/reject` - Driver rejeita
- `POST /api/ride-requests/{id}/start` - Enterprise inicia

### Notificações
- `GET /api/notifications/{user_id}` - Lista notificações
- `POST /api/notifications/{user_id}/{notif_id}/read` - Marcar como lida

### Contratos (Compatibilidade v1)
- `POST /contract/create` - Criar contrato Stellar
- `GET /contract/{trip_id}` - Status do contrato
- `POST /contract/manage` - Atualizar status

## 👥 Usuários Demo

O sistema inclui usuários de demonstração:

**Motoristas:**
- João Silva (DRV-001)
- Maria Santos (DRV-002)

**Empresas:**
- TransLog Empresa (EMP-001)

**Admin:**
- Sistema Admin (ADM-001)

## 🔄 Estados da Corrida

```
Pendente → [Driver aceita] → Aceito → [Enterprise inicia] → EmAndamento → Finalizado
         → [Driver recusa] → Recusado
         → [Timeout/Cancel] → Cancelado
```

## 🔔 Sistema de Notificações

- **Enterprise**: Recebe notificações quando driver aceita/rejeita
- **Driver**: Recebe notificações de novas corridas disponíveis
- **Polling**: Atualizações automáticas a cada 10-15 segundos
- **Badges**: Contadores visuais de notificações não lidas

## 🔒 Controle de Permissões

- **Driver**: Pode aceitar/rejeitar apenas suas próprias corridas
- **Enterprise**: Pode criar corridas e gerenciar suas próprias solicitações
- **Admin**: Acesso total (futuro)

## 🌐 Blockchain Stellar

- Contratos criados quando corrida é **iniciada** (não na solicitação)
- Smart contract Soroban para checkpoints
- Transações registradas na rede testnet/mainnet
- Histórico imutável de eventos

## 🛣️ Roadmap

### Próximas Funcionalidades
- [ ] WebSockets para notificações real-time
- [ ] Autenticação JWT
- [ ] Persistência em banco de dados
- [ ] Sistema de pagamentos
- [ ] Tracking GPS em tempo real
- [ ] Dashboard de analytics
- [ ] API para apps móveis

### Melhorias Técnicas
- [ ] Testes unitários/integração
- [ ] Docker containerização
- [ ] CI/CD pipeline
- [ ] Monitoramento e logs
- [ ] Rate limiting
- [ ] Caching Redis

## 🚨 Limitações Atuais

- **Dados em memória**: Reiniciar servidor apaga dados
- **Polling**: Não é real-time (WebSockets futuros)
- **Sem autenticação**: Sistema baseado em seleção de usuário
- **Stellar simulado**: Funciona sem contrato real deployed

## 🆘 Troubleshooting

### Problema: Motoristas não aparecem
- Verifique se `/api/users?role=driver` retorna dados
- Confirme inicialização do `user_service`

### Problema: Notificações não atualizam
- Verifique polling no console do navegador
- Confirme seleção de usuário ativo

### Problema: Erro ao criar corrida
- Verifique se empresa e motorista estão selecionados
- Confirme campos obrigatórios preenchidos

## 📞 Suporte

Para problemas ou dúvidas:
1. Verificar logs do servidor
2. Inspecionar Network tab do navegador
3. Confirmar configuração .env
4. Testar endpoints via `/docs` (Swagger)

---

**SENTRA Transport Platform v2.0** - Powered by Stellar Network