#![no_std]
use soroban_sdk::{contract, contractimpl, symbol_short, Env, String, Symbol};

#[contract]
pub struct LogisticsContract;


#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[soroban_sdk::contracttype]
pub enum TripStatus {
    Saida,
    Meio,
    Entrada,
}

const TRIP_ID: Symbol = symbol_short!("TRIP_ID");
const STATUS: Symbol = symbol_short!("STATUS");

#[contractimpl]
impl LogisticsContract {
    pub fn criar_viagem(env: Env, trip_id: String) {
        env.storage().instance().set(&TRIP_ID, &trip_id);
        env.storage()
            .instance()
            .set(&STATUS, &TripStatus::Saida);
    }

    pub fn marcar_meio(env: Env, trip_id: String) {
        let current_trip_id: String = env.storage().instance().get(&TRIP_ID).unwrap();
        if current_trip_id != trip_id {
            panic!("Trip ID mismatch");
        }

        let status: TripStatus = env.storage().instance().get(&STATUS).unwrap();
        match status {
            TripStatus::Saida => env.storage().instance().set(&STATUS, &TripStatus::Meio),
            _ => panic!("Invalid status transition"),
        }
    }

    pub fn marcar_entrada(env: Env, trip_id: String) {
        let current_trip_id: String = env.storage().instance().get(&TRIP_ID).unwrap();
        if current_trip_id != trip_id {
            panic!("Trip ID mismatch");
        }

        let status: TripStatus = env.storage().instance().get(&STATUS).unwrap();
        match status {
            TripStatus::Meio => env
                .storage()
                .instance()
                .set(&STATUS, &TripStatus::Entrada),
            _ => panic!("Invalid status transition"),
        }
    }

    pub fn obter_status(env: Env, trip_id: String) -> TripStatus {
        let current_trip_id: String = env.storage().instance().get(&TRIP_ID).unwrap();
        if current_trip_id != trip_id {
            panic!("Trip ID mismatch");
        }
        env.storage().instance().get(&STATUS).unwrap()
    }
}
