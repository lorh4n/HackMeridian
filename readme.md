# SENTRA Transport Platform

[![Deploy](https://img.shields.io/badge/Deploy-Render-blue)](https://hackmeridian-1.onrender.com)

**SENTRA** is a decentralized transport platform that leverages the Stellar blockchain to create a transparent and efficient system for managing ride requests between enterprises and drivers.

## 🚀 Live Demo

You can access the live application here: [https://hackmeridian-1.onrender.com](https://hackmeridian-1.onrender.com)

## 📖 About the Project

This project was developed for the HackMeridian hackathon. It aims to solve the problem of opacity and centralization in the transport logistics industry. By using smart contracts on the Stellar network, SENTRA ensures that all parties have a single source of truth for ride events, from creation to completion.

The platform provides separate interfaces for two main roles:
- **Enterprise**: Can create and manage ride requests.
- **Driver**: Can view and accept pending ride requests.

## ✨ Features

- **Decentralized Workflow**: Smart contracts on the Stellar blockchain manage the state of each ride.
- **Real-time Notifications**: A notification system keeps users informed of ride status changes.
- **Role-based Interfaces**: Separate and intuitive UIs for enterprises and drivers.
- **Complete Ride Lifecycle**: Full management of the ride process, from request to completion.

## 🛠️ Technologies Used

- **Backend**: Python, FastAPI
- **Frontend**: HTML, CSS, JavaScript, Jinja2
- **Blockchain**: Stellar SDK, Soroban (with Rust)
- **Deployment**: Render

## 🧠 Smart Contract

The core of the platform's decentralized logic lies in a smart contract developed with Rust using the Soroban SDK for the Stellar network.

This contract is responsible for managing the lifecycle of a trip through various checkpoints. Each trip has a defined status, which can be one of the following:

- `Pendente`: The trip has been created but has not yet started.
- `EmAndamento`: The trip has started.
- `PontoIntermediario`: The trip has reached an intermediate checkpoint.
- `Finalizada`: The trip has been completed.

The main functions of the contract are:

- `criar_viagem`: Creates a new trip with defined checkpoints (start, middle, and end).
- `marcar_saida`: Marks the trip as started.
- `marcar_meio`: Marks the trip as having reached the intermediate point.
- `marcar_chegada`: Marks the trip as finished.

Each of these functions requires authorization from the corresponding checkpoint address, ensuring that only authorized entities can update the trip status. This creates an immutable and verifiable history of each trip on the blockchain.

## 🏁 Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

- Python 3.8+
- An account on the Stellar test network.

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/your_username/HackMeridian.git
   ```
2. Navigate to the backend directory
   ```sh
   cd HackMeridian/backend
   ```
3. Install Python packages
   ```sh
   pip install -r requirements.txt
   ```
4. Create a `.env` file from the example
    ```sh
    cp .env.example .env
    ```
5. Add your Stellar secret key to the `.env` file.

### Running the Application

1. Run the FastAPI server
   ```sh
   uvicorn main:app --reload
   ```
2. Open your browser and navigate to `http://127.0.0.1:8000`.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.