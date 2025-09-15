use axum::{routing::get, Router, Json, serve};
use serde::Serialize;
use std::net::SocketAddr;
use tower_http::cors::{Any, CorsLayer}; // <-- ADICIONE ESTAS LINHAS
use axum::http::HeaderValue;

#[derive(Serialize)]
struct Message {
    message: String,
}

async fn hello_world() -> Json<Message> {
    Json(Message {
        message: "Hello, World from Rust!".to_string(),
    })
}

#[tokio::main]
async fn main() {
    // Obtenha a URL do seu frontend a partir de uma variável de ambiente ou use um valor fixo
    let frontend_url = "https://hack-meridian-chi.vercel.app/"; // <-- SUBSTITUA PELO SEU URL

    let app = Router::new()
        .route("/hello", get(hello_world))
        .layer(
            CorsLayer::new()
                // ANTES: .allow_origin(Any)
                // DEPOIS:
                .allow_origin(frontend_url.parse::<HeaderValue>().unwrap())
                .allow_methods(Any)
                .allow_headers(Any)
        );

    // endereço localhost:3000
    let addr = SocketAddr::from(([0, 0, 0, 0], 3000));
    println!("Servidor rodando em http://{}", addr);

    // Cria o listener TCP
    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    
    // Serve a aplicação
    serve(listener, app).await.unwrap();
}