// Configuração da API - ajuste para seu ambiente
const API_URL = "https://hackmeridian-1.onrender.com"; // ou sua URL do Render/Railway

// Estado global para sincronizar com o trip viewer
let currentTripData = null;
let tripState = {
  registered: false,
  active: false
};

/**
 * Cria um novo contrato de transporte usando os dados do formulário
 */
async function createContract() {
  try {
    // Se não temos dados do formulário, usa dados de exemplo
    if (!currentTripData) {
      console.warn("Usando dados de exemplo - formulário não preenchido");
      currentTripData = {
        trip_id: "TRIP-EXAMPLE-001",
        driver: "DRIVER-007",
        origin: "Rio de Janeiro, RJ",
        destination: "São Paulo, SP"
      };
    }

    // Converte dados do formulário para o formato esperado pelo backend
    const tripData = {
      trip_id: currentTripData.trip_id,
      driver: currentTripData.driver,
      route: [
        currentTripData.origin,
        "Checkpoint Intermediário", // Ponto intermediário padrão
        currentTripData.destination
      ]
    };

    showLoading("Criando contrato na blockchain...");

    const response = await fetch(`${API_URL}/contract/create`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify(tripData),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || `Erro HTTP: ${response.status}`);
    }

    if (data.success) {
      tripState.registered = true;
      showOutput("✅ Contrato criado com sucesso!", data.data);
      
      // Atualiza o trip viewer se disponível
      updateTripViewer(data.data);
      
      // Habilita botões de controle
      enableControlButtons();
    } else {
      throw new Error(data.message || "Falha ao criar contrato");
    }

  } catch (error) {
    console.error("Erro ao criar contrato:", error);
    showOutput("❌ Erro ao criar contrato", {
      error: error.message,
      details: "Verifique se o backend está rodando e acessível"
    });
  } finally {
    hideLoading();
  }
}

/**
 * Atualiza o status do contrato (checkpoints da viagem)
 */
async function manageContract(event = "checkpoint", status = "ok") {
  try {
    if (!currentTripData || !tripState.registered) {
      throw new Error("Nenhuma viagem registrada. Crie um contrato primeiro.");
    }

    const update = {
      trip_id: currentTripData.trip_id,
      event: event,
      status: status,
      location: "Localização atual", // Poderia ser obtida via GPS
      timestamp: new Date().toISOString()
    };

    showLoading(`Atualizando contrato - ${event}...`);

    const response = await fetch(`${API_URL}/contract/manage`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify(update),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || `Erro HTTP: ${response.status}`);
    }

    if (data.success) {
      showOutput(`✅ ${data.message}`, data.data);
      
      // Atualiza estado local
      if (event === "saida") {
        tripState.active = true;
      } else if (event === "chegada") {
        tripState.active = false;
      }
      
      // Atualiza o trip viewer
      updateTripViewer(data.data);
    } else {
      throw new Error(data.message || "Falha ao atualizar contrato");
    }

  } catch (error) {
    console.error("Erro ao atualizar contrato:", error);
    showOutput("❌ Erro ao atualizar contrato", {
      error: error.message,
      event: event,
      status: status
    });
  } finally {
    hideLoading();
  }
}

/**
 * Visualiza o estado atual do contrato
 */
async function viewContract() {
  try {
    if (!currentTripData) {
      throw new Error("Nenhuma viagem selecionada");
    }

    showLoading("Consultando blockchain...");

    const response = await fetch(`${API_URL}/contract/${currentTripData.trip_id}`, {
      method: "GET",
      headers: {
        "Accept": "application/json"
      }
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || `Erro HTTP: ${response.status}`);
    }

    if (data.success) {
      showOutput("📋 Estado atual do contrato:", data.data);
      
      // Atualiza trip viewer com dados atualizados
      updateTripViewer(data.data);
    } else {
      throw new Error(data.message || "Contrato não encontrado");
    }

  } catch (error) {
    console.error("Erro ao consultar contrato:", error);
    showOutput("❌ Erro ao visualizar contrato", {
      error: error.message,
      trip_id: currentTripData?.trip_id
    });
  } finally {
    hideLoading();
  }
}

/**
 * Funções específicas para cada checkpoint da viagem
 */
async function marcarSaida() {
  await manageContract("saida", "ok");
}

async function marcarCheckpointIntermediario() {
  await manageContract("meio", "checkpoint");
}

async function marcarChegada() {
  await manageContract("chegada", "completed");
}

/**
 * Obtém dados do formulário do trip viewer (se disponível)
 */
function getTripDataFromForm() {
  const formTripId = document.getElementById('form-trip-id');
  const formDriverId = document.getElementById('form-driver-id');
  const originInput = document.getElementById('origin');
  const destinationInput = document.getElementById('destination');

  if (formTripId && formDriverId && originInput && destinationInput) {
    return {
      trip_id: formTripId.value,
      driver: formDriverId.value,
      origin: originInput.value,
      destination: destinationInput.value
    };
  }

  return null;
}

/**
 * Atualiza o trip viewer com dados do contrato
 */
function updateTripViewer(contractData) {
  try {
    // Atualiza campos do summary se existirem
    const summaryTripId = document.getElementById('summary-trip-id');
    const summaryDriverId = document.getElementById('summary-driver-id');
    const summaryStatus = document.getElementById('summary-status');

    if (summaryTripId) summaryTripId.textContent = contractData.trip_id || 'N/A';
    if (summaryDriverId) summaryDriverId.textContent = contractData.driver || 'N/A';
    if (summaryStatus) {
      // Mapeia status do backend para status do frontend
      const statusMap = {
        'Pendente': 'IDLE',
        'EmAndamento': 'IN_PROGRESS', 
        'PontoIntermediario': 'IN_PROGRESS',
        'Finalizada': 'COMPLETED'
      };
      summaryStatus.textContent = statusMap[contractData.status] || contractData.status || 'IDLE';
    }

    // Adiciona evento ao log se houver checkpoints novos
    if (contractData.checkpoints && contractData.checkpoints.length > 0) {
      const latestCheckpoint = contractData.checkpoints[contractData.checkpoints.length - 1];
      addEventToLog(latestCheckpoint);
    }

  } catch (error) {
    console.warn("Trip viewer não disponível ou erro ao atualizar:", error);
  }
}

/**
 * Adiciona evento ao log do trip viewer
 */
function addEventToLog(checkpoint) {
  try {
    const eventLogList = document.getElementById('event-log-list');
    const emptyLogMsg = document.getElementById('empty-log-msg');

    if (!eventLogList) return;

    // Remove mensagem vazia se existir
    if (emptyLogMsg) {
      emptyLogMsg.remove();
    }

    // Cria novo item do log
    const logItem = document.createElement('li');
    logItem.className = "flex items-start text-sm p-3 rounded-md bg-blue-50 border-blue-200";
    logItem.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5 mr-3 text-blue-500 flex-shrink-0">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="16" x2="12" y2="12"></line>
        <line x1="12" y1="8" x2="12.01" y2="8"></line>
      </svg>
      <div>
        <p class="font-semibold text-blue-700">Checkpoint: ${checkpoint.event}</p>
        <p class="text-gray-600">Status: ${checkpoint.status}</p>
        <span class="font-mono text-xs text-gray-400 mt-1 block">${new Date(checkpoint.timestamp).toLocaleString()}</span>
      </div>
    `;

    eventLogList.appendChild(logItem);

  } catch (error) {
    console.warn("Erro ao adicionar evento ao log:", error);
  }
}

/**
 * Verifica saúde da API
 */
async function checkApiHealth() {
  try {
    const response = await fetch(`${API_URL}/health`);
    const data = await response.json();
    
    showOutput("🔍 Status da API:", data);
    
    return data.status === "healthy";

  } catch (error) {
    showOutput("❌ API indisponível", {
      error: error.message,
      url: API_URL
    });
    return false;
  }
}

/**
 * Habilita botões de controle após criar contrato
 */
function enableControlButtons() {
  const controlButtons = [
    'btn-start', 'btn-next', 'btn-end', 
    'btn-saida', 'btn-meio', 'btn-chegada'
  ];
  
  controlButtons.forEach(id => {
    const button = document.getElementById(id);
    if (button) {
      button.disabled = false;
      button.classList.remove('opacity-50', 'cursor-not-allowed');
    }
  });
}

/**
 * Funções de UI para feedback visual
 */
function showOutput(title, content) {
  const output = document.getElementById("output");
  if (output) {
    const timestamp = new Date().toLocaleTimeString();
    output.innerHTML = `
      <div class="mb-4 p-4 border rounded-lg">
        <div class="flex justify-between items-center mb-2">
          <h3 class="font-bold text-lg">${title}</h3>
          <span class="text-xs text-gray-500">${timestamp}</span>
        </div>
        <pre class="bg-gray-100 p-3 rounded text-sm overflow-auto">${JSON.stringify(content, null, 2)}</pre>
      </div>
    ` + (output.innerHTML || '');
  } else {
    console.log(title, content);
  }
}

function showLoading(message) {
  const loadingDiv = document.getElementById("loading") || createLoadingDiv();
  loadingDiv.textContent = message;
  loadingDiv.style.display = "block";
}

function hideLoading() {
  const loadingDiv = document.getElementById("loading");
  if (loadingDiv) {
    loadingDiv.style.display = "none";
  }
}

function createLoadingDiv() {
  const loading = document.createElement("div");
  loading.id = "loading";
  loading.className = "fixed top-4 right-4 bg-blue-500 text-white px-4 py-2 rounded shadow-lg";
  loading.style.display = "none";
  document.body.appendChild(loading);
  return loading;
}

/**
 * Inicialização quando o DOM estiver pronto
 */
document.addEventListener('DOMContentLoaded', () => {
  console.log("App.js carregado - Integrando com trip viewer...");
  
  // Tenta obter dados do formulário imediatamente
  currentTripData = getTripDataFromForm();
  
  // Se temos acesso ao botão de salvar viagem, intercepta o clique
  const saveTripBtn = document.getElementById('saveTripBtn');
  if (saveTripBtn) {
    saveTripBtn.addEventListener('click', () => {
      // Pequeno delay para garantir que os dados foram atualizados
      setTimeout(() => {
        currentTripData = getTripDataFromForm();
        console.log("Dados da viagem capturados:", currentTripData);
      }, 100);
    });
  }

  // Adiciona event listeners para botões de checkpoint se existirem
  const btnSaida = document.getElementById('btn-saida');
  const btnMeio = document.getElementById('btn-meio'); 
  const btnChegada = document.getElementById('btn-chegada');

  if (btnSaida) btnSaida.addEventListener('click', marcarSaida);
  if (btnMeio) btnMeio.addEventListener('click', marcarCheckpointIntermediario);
  if (btnChegada) btnChegada.addEventListener('click', marcarChegada);

  // Verifica saúde da API na inicialização
  checkApiHealth();
});

// Exporta funções para uso global
if (typeof window !== 'undefined') {
  window.createContract = createContract;
  window.manageContract = manageContract;
  window.viewContract = viewContract;
  window.marcarSaida = marcarSaida;
  window.marcarCheckpointIntermediario = marcarCheckpointIntermediario;
  window.marcarChegada = marcarChegada;
  window.checkApiHealth = checkApiHealth;
}