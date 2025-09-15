// main.rs

use axum::{routing::get, Router, Json, serve};
use serde::Serialize;
use std::net::SocketAddr;
use tower_http::cors::{Any, CorsLayer};
use axum::http::{HeaderValue, StatusCode};
use std::env;

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

    let app = Router::new()
        .route("/", get(root))
        .route("/hello", get(hello_world))
        .layer(
            CorsLayer::new()
                .allow_origin([
                     "https://hack-meridian-chi.vercel.app".parse::<HeaderValue>().unwrap(),
                    "http://localhost:3000".parse::<HeaderValue>().unwrap(), // para desenvolvimento local
                ])
                .allow_methods(Any)
                .allow_headers(Any)
        );

    // Pega a porta do ambiente (Render define automaticamente) ou usa 3000 como padrão
    let port = env::var("PORT").unwrap_or_else(|_| "3000".to_string());
    let port: u16 = port.parse().expect("PORT deve ser um número válido");
    
    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    println!("Servidor rodando em http://{}", addr);

    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    
    serve(listener, app).await.unwrap();
}