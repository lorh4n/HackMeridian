// models.rs

use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
pub struct TripData {
    pub trip_id: String,
    pub driver: String,
    pub route: Vec<String>,
}

#[derive(Deserialize)]
pub struct ContractUpdate {
    pub trip_id: String,
    pub event: String,
    pub status: String,
}

#[derive(Serialize)]
pub struct ContractStatus {
    pub trip_id: String,
    pub status: String,
}

#[derive(Serialize)]
pub struct ApiResponse {
    pub message: String,
    pub data: Option<serde_json::Value>,
}