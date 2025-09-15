use anyhow::Result;
use axum::{extract::Path, http::StatusCode, response::Json};
use serde_json::json;
use soroban_sdk::xdr::{ScVal, WriteXdr, TransactionEnvelope, Limited};
use std::env;

use reqwest::Client as HttpClient;
use serde::{Deserialize, Serialize};

use axum::debug_handler;

use crate::models::{ApiResponse, ContractUpdate, TripData};

pub struct SorobanClient {
    rpc_url: String,
    contract_id: String,
    secret_key: String,
    http_client: HttpClient,
}

#[derive(Serialize)]
struct RpcRequest {
    jsonrpc: String,
    id: u32,
    method: String,
    params: serde_json::Value,
}

#[derive(Deserialize)]
struct RpcResponse {
    result: Option<serde_json::Value>,
    error: Option<serde_json::Value>,
}

impl SorobanClient {
    fn new(rpc_url: String, contract_id: String, secret_key: String) -> Self {
        Self {
            rpc_url,
            contract_id,
            secret_key,
            http_client: HttpClient::new(),
        }
    }

    async fn invoke_contract(&self, function_name: &str, args: Vec<ScVal>) -> Result<serde_json::Value> {
        // Dummy envelope só para compilar
        let dummy_envelope = TransactionEnvelope::default();

        // Cria o Limited com limite de 10MB
        let mut limited = Limited::new(Vec::new(), 10_000_000);
        dummy_envelope.write_xdr(&mut limited)?;

        // Recupera o Vec<u8> de dentro do Limited usando deref
        let buf: Vec<u8> = *limited;
        let xdr_base64 = base64::encode(&buf);

        let request = RpcRequest {
            jsonrpc: "2.0".to_string(),
            id: 1,
            method: "simulateTransaction".to_string(),
            params: json!({
                "transaction": xdr_base64
            }),
        };

        let response = self
            .http_client
            .post(&self.rpc_url)
            .json(&request)
            .send()
            .await?;

        let rpc_response: RpcResponse = response.json().await?;

        if let Some(error) = rpc_response.error {
            return Err(anyhow::anyhow!("RPC Error: {:?}", error));
        }

        Ok(rpc_response.result.unwrap_or_default())
    }
}

async fn get_soroban_client() -> Result<SorobanClient> {
    dotenvy::dotenv().ok();
    let rpc_url = env::var("SOROBAN_RPC_URL")?;
    let contract_id = env::var("CONTRACT_ID")?;
    let secret_key = env::var("SECRET_KEY")?;

    Ok(SorobanClient::new(rpc_url, contract_id, secret_key))
}

pub async fn view_contract(Path(trip_id): Path<String>) -> (StatusCode, Json<ApiResponse>) {
    println!("Viewing contract for trip: {}", trip_id);

    match get_soroban_client().await {
        Ok(client) => {
            // transforma trip_id em ScVal
            let arg = ScVal::Symbol(trip_id.clone().try_into().unwrap());
            let args = vec![arg];

            let result = client.invoke_contract("obter_status", args).await;

            match result {
                Ok(val) => {
                    let response = ApiResponse {
                        message: "Status do contrato obtido com sucesso!".to_string(),
                        data: Some(json!({ "trip_id": trip_id, "status": format!("{:?}", val) })),
                    };
                    (StatusCode::OK, Json(response))
                }
                Err(e) => {
                    let response = ApiResponse {
                        message: format!("Erro ao chamar o contrato: {:?}", e),
                        data: None,
                    };
                    (StatusCode::INTERNAL_SERVER_ERROR, Json(response))
                }
            }
        }
        Err(e) => {
            let response = ApiResponse {
                message: format!("Erro de configuração do cliente: {:?}", e),
                data: None,
            };
            (StatusCode::INTERNAL_SERVER_ERROR, Json(response))
        }
    }
}
