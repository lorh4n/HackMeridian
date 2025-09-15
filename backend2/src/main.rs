// main.rs

mod models;
mod routes;
mod soroban_client;

use axum::serve;
use std::net::SocketAddr;
use tower_http::cors::{Any, CorsLayer};
use axum::http::HeaderValue;
use std::env;

#[tokio::main]
async fn main() {

    let app = routes::create_routes()
        .layer(
            CorsLayer::new()
                .allow_origin([
                     "https://hack-meridian-chi.vercel.app".parse::<HeaderValue>().unwrap(),
                    "http://localhost:3000".parse::<HeaderValue>().unwrap(), // para desenvolvimento local
                    "http://127.0.0.1:5500".parse::<HeaderValue>().unwrap(),
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