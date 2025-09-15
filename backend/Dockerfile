# --- Estágio 1: Build ---
# Usamos uma imagem oficial do Rust como base para compilar o projeto
FROM rust:1.79-slim-bullseye AS builder

# Define o diretório de trabalho dentro do contêiner
WORKDIR /usr/src/app

# Copia os arquivos do projeto para o contêiner
COPY . .

# Compila o projeto em modo "release" para otimização máxima
RUN cargo build --release

# --- Estágio 2: Final ---
# Usamos uma imagem mínima do Debian para a versão final, deixando-a leve
FROM debian:bullseye-slim

# Copia apenas o binário compilado do estágio de build
COPY --from=builder /usr/src/app/target/release/backend /usr/local/bin/backend

# Expõe a porta 3000, que é a que seu app Axum usa
EXPOSE 3000

# O comando para iniciar o servidor quando o contêiner rodar
CMD ["backend"]