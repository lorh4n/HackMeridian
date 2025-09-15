backend/
 ├── Cargo.toml
 └── src/
     ├── main.rs
     ├── routes.rs
     ├── soroban_client.rs
     └── models.rs

Estrutura dos arquivos:
- main.rs: inicia o servidor e monta rotas.
- routes.rs: define endpoints REST.
- soroban_client.rs: funções que interagem com Soroban (deploy, invoke, query).
- models.rs: structs para serialização/deserialização JSON.