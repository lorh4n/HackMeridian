const API_URL = "http://localhost:3000"; // troque para o backend no Render

async function createContract() {
  const tripData = {
    trip_id: "TRIP-001",
    driver: "DRIVER-123",
    route: ["lat1,lng1", "lat2,lng2"],
  };

  try {
    const res = await fetch(`${API_URL}/contract/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(tripData),
    });
    const data = await res.json();
    showOutput("Contrato criado!", data);
  } catch (err) {
    showOutput("Erro ao criar contrato", err);
  }
}

async function manageContract() {
  const update = {
    trip_id: "TRIP-001",
    event: "checkpoint",
    status: "ok"
  };

  try {
    const res = await fetch(`${API_URL}/contract/manage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update),
    });
    const data = await res.json();
    showOutput("Contrato atualizado!", data);
  } catch (err) {
    showOutput("Erro ao gerir contrato", err);
  }
}

async function viewContract() {
  const tripId = "TRIP-001";

  try {
    const res = await fetch(`${API_URL}/contract/${tripId}`);
    const data = await res.json();
    showOutput("Situação do contrato:", data);
  } catch (err) {
    showOutput("Erro ao visualizar contrato", err);
  }
}

function showOutput(title, content) {
  const output = document.getElementById("output");
  output.innerHTML = `<h3>${title}</h3><pre>${JSON.stringify(content, null, 2)}</pre>`;
}
