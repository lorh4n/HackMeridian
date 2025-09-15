use axum::{routing::get, Router, Json, serve};
use serde::Serialize;
use std::net::SocketAddr;
use tower_http::cors::{Any, CorsLayer}; // <-- ADICIONE ESTAS LINHAS

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
    // cria rota /hello com middleware CORS
    let app = Router::new()
        .route("/hello", get(hello_world))
        .layer(
            CorsLayer::new()
                .allow_origin(Any)
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