use axum::{
    routing::{get},
    Router,
};

use crate::soroban_client::{view_contract};

pub fn create_routes() -> Router {
    Router::new()
        .route("/", get(root))
        .route("/contract/:contract_id", get(view_contract))
}

async fn root() -> &'static str {
    "API is running!"
}

