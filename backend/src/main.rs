// main.rs

use axum::{routing::get, Router, Json, serve};
use serde::Serialize;
use std::net::SocketAddr;
use tower_http::cors::{Any, CorsLayer};
use axum::http::{HeaderValue, StatusCode}; // <-- ADICIONE StatusCode

#[derive(Serialize)]
struct Message {
    message: String,
}

// NOVA FUNÇÃO PARA A ROTA RAIZ
async fn root() -> (StatusCode, &'static str) {
    (StatusCode::OK, "API is running!")
}

async fn hello_world() -> Json<Message> {
    Json(Message {
        message: "Hello, World from Rust!".to_string(),
    })
}

#[tokio::main]
async fn main() {
    let frontend_url = "https://hack-meridian-chi.vercel.app/";

    let app = Router::new()
        .route("/", get(root)) // <-- ADICIONE ESTA LINHA PARA A ROTA RAIZ
        .route("/hello", get(hello_world))
        .layer(
            CorsLayer::new()
                .allow_origin(frontend_url.parse::<HeaderValue>().unwrap())
                .allow_methods(Any)
                .allow_headers(Any)
        );

    let addr = SocketAddr::from(([0, 0, 0, 0], 3000));
    println!("Servidor rodando em http://{}", addr);

    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    
    serve(listener, app).await.unwrap();
}