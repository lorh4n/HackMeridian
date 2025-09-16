# 📦 Deploy do Smart Contract Soroban

Instruções para fazer deploy do smart contract de checkpoints na rede Stellar.

## 🔧 Pré-requisitos

1. **Rust e Soroban CLI instalados**
```bash
# Instalar Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Instalar Soroban CLI
cargo install --locked soroban-cli
```

2. **Conta Stellar configurada**
```bash
# Gerar nova identidade
soroban keys generate --network testnet --name deployer

# Financiar conta (testnet)
soroban keys fund deployer --network testnet
```

## 🚀 Deploy do Contrato

### 1. Compilar o Contrato

```bash
# No diretório do smart contract
soroban contract build
```

### 2. Deploy

```bash
# Deploy na testnet
soroban contract deploy \
  --network testnet \
  --source deployer \
  --wasm target/wasm32-unknown-unknown/release/trip_checkpoints.wasm

# Salve o CONTRACT_ID retornado!
```

### 3. Inicializar Contrato

```bash
# Inicializar com sua conta como admin
soroban contract invoke \
  --network testnet \
  --source deployer \
  --id SEU_CONTRACT_ID \
  -- initialize \
  --admin $(soroban keys address deployer)
```

### 4. Testar Contrato

```bash
# Criar uma viagem de teste
soroban contract invoke \
  --network testnet \
  --source deployer \
  --id SEU_CONTRACT_ID \
  -- criar_viagem \
  --trip_id "TRIP-TEST-001" \
  --saida_checkpoint $(soroban keys address deployer) \
  --meio_checkpoint $(soroban keys address deployer) \
  --chegada_checkpoint $(soroban keys address deployer)

# Verificar viagem criada
soroban contract invoke \
  --network testnet \
  --source deployer \
  --id SEU_CONTRACT_ID \
  -- get_viagem \
  --trip_id "TRIP-TEST-001"
```

## 🔄 Integração com Backend

Após o deploy, atualize seu `.env`:

```bash
STELLAR_CONTRACT_ID=SEU_CONTRACT_ID_AQUI
STELLAR_SECRET_KEY=sua_secret_key_deployer
STELLAR_PUBLIC_KEY=sua_public_key_deployer
```

## 📝 Funções Disponíveis

### Administrativas
- `initialize(admin: Address)` - Inicializa contrato
- `get_admin()` - Retorna admin atual

### Gestão de Viagens
- `criar_viagem(trip_id, saida_checkpoint, meio_checkpoint, chegada_checkpoint)` - Cria nova viagem
- `get_viagem(trip_id)` - Consulta viagem

### Checkpoints
- `marcar_saida(trip_id)` - Marca saída (Pendente → EmAndamento)
- `marcar_meio(trip_id)` - Marca checkpoint intermediário (EmAndamento → PontoIntermediario)  
- `marcar_chegada(trip_id)` - Marca chegada (PontoIntermediario → Finalizada)

## 🔐 Segurança

- Cada checkpoint deve ser autorizado pelo endereço correspondente
- Admin pode criar viagens
- Status seguem ordem: Pendente → EmAndamento → PontoIntermediario → Finalizada
- Transições inválidas geram erro `EstadoInvalido`

## 🏭 Para Produção (Mainnet)

```bash
# Configure para mainnet
soroban keys generate --network mainnet --name deployer-prod
soroban keys fund deployer-prod --network mainnet  # Use Stellar Laboratory

# Deploy
soroban contract deploy \
  --network mainnet \
  --source deployer-prod \
  --wasm target/wasm32-unknown-unknown/release/trip_checkpoints.wasm

# Atualize .env
STELLAR_NETWORK=mainnet
STELLAR_CONTRACT_ID=seu_contract_id_mainnet
```

## 📊 Monitoramento

Use o endpoint `/health` do backend para verificar:
- Conexão com Stellar
- Status do contrato  
- Última sincronização