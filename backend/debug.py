#!/usr/bin/env python3
"""
Script de debug para testar a criação de ride requests
"""

import requests
import json
import sys

# Configuração
BASE_URL = "http://0.0.0.0:3000"  # ou http://0.0.0.0:3000

def test_api_connection():
    """Testa se a API está respondendo"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✓ API Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  - Status: {data.get('status')}")
            print(f"  - Users: {data.get('users_count')}")
            print(f"  - Ride Requests: {data.get('ride_requests_count')}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Erro de conexão: {e}")
        return False

def test_get_users():
    """Testa busca de usuários"""
    try:
        print("\n--- Testando busca de usuários ---")
        
        # Todos os usuários
        response = requests.get(f"{BASE_URL}/api/users")
        print(f"GET /api/users: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            users = data.get('data', {}).get('users', [])
            print(f"Total de usuários: {len(users)}")
            for user in users:
                print(f"  - {user['id']}: {user['name']} ({user['role']})")
        
        # Empresas
        response = requests.get(f"{BASE_URL}/api/users?role=enterprise")
        print(f"GET /api/users?role=enterprise: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            enterprises = data.get('data', {}).get('users', [])
            print(f"Empresas encontradas: {len(enterprises)}")
            
        # Motoristas
        response = requests.get(f"{BASE_URL}/api/users?role=driver")
        print(f"GET /api/users?role=driver: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            drivers = data.get('data', {}).get('users', [])
            print(f"Motoristas encontrados: {len(drivers)}")
            
        return enterprises, drivers
            
    except Exception as e:
        print(f"✗ Erro ao buscar usuários: {e}")
        return [], []

def test_create_ride_request(enterprise_id, driver_id):
    """Testa criação de ride request"""
    print(f"\n--- Testando criação de ride request ---")
    
    # Dados do request exatamente como no frontend
    request_data = {
        "enterprise_id": enterprise_id,
        "driver_id": driver_id,
        "trip_data": {
            "trip_id": "TRIP-123456-ABC",
            "driver": driver_id,
            "route": ["-23.550000,-46.633000", "-23.555000,-46.640000", "-23.560000,-46.650000"],
            "origin_address": "Rio de Janeiro, RJ",
            "destination_address": "São Paulo, SP",
            "estimated_duration": 360
        }
    }
    
    print("Dados enviados:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/ride-requests",
            headers={"Content-Type": "application/json"},
            json=request_data
        )
        
        print(f"\nResposta HTTP: {response.status_code}")
        print("Headers da resposta:", dict(response.headers))
        
        try:
            response_data = response.json()
            print("Corpo da resposta:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except:
            print("Corpo da resposta (texto):")
            print(response.text)
            
        return response.status_code == 200 or response.status_code == 201
        
    except Exception as e:
        print(f"✗ Erro na requisição: {e}")
        return False

def test_pydantic_validation():
    """Testa validação dos modelos Pydantic"""
    print(f"\n--- Testando validação Pydantic ---")
    
    # Testa com dados inválidos para ver os erros de validação
    invalid_requests = [
        {
            "enterprise_id": "",  # Vazio
            "driver_id": "DRV-001",
            "trip_data": {
                "trip_id": "TRIP-123",
                "driver": "DRV-001",
                "route": ["-23.550000,-46.633000"]
            }
        },
        {
            "enterprise_id": "EMP-001",
            "driver_id": "",  # Vazio
            "trip_data": {
                "trip_id": "TRIP-123",
                "driver": "DRV-001", 
                "route": ["-23.550000,-46.633000"]
            }
        },
        {
            "enterprise_id": "EMP-001",
            "driver_id": "DRV-001",
            "trip_data": {
                "trip_id": "",  # Vazio
                "driver": "DRV-001",
                "route": ["-23.550000,-46.633000"]
            }
        }
    ]
    
    for i, invalid_data in enumerate(invalid_requests):
        print(f"\nTeste {i+1} - Dados inválidos:")
        try:
            response = requests.post(
                f"{BASE_URL}/api/ride-requests",
                headers={"Content-Type": "application/json"},
                json=invalid_data
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 422:
                error_data = response.json()
                print("Erros de validação:")
                for error in error_data.get('detail', []):
                    print(f"  - {error.get('loc', [])}: {error.get('msg', '')}")

        except Exception as e:
            print(f"  Erro: {e}")

def main():
    print("🔍 SCRIPT DE DEBUG - RIDE REQUESTS\n")
    
    # 1. Testar conexão
    if not test_api_connection():
        print("❌ API não está acessível. Verifique se o servidor está rodando.")
        sys.exit(1)
    
    # 2. Buscar usuários
    enterprises, drivers = test_get_users()
    
    if not enterprises:
        print("❌ Nenhuma empresa encontrada")
        sys.exit(1)
        
    if not drivers:
        print("❌ Nenhum motorista encontrado")
        sys.exit(1)
    
    # 3. Testar criação com dados válidos
    enterprise_id = enterprises[0]['id']
    driver_id = drivers[0]['id']
    
    print(f"\n🚀 Tentando criar ride request:")
    print(f"  Enterprise: {enterprise_id}")
    print(f"  Driver: {driver_id}")
    
    success = test_create_ride_request(enterprise_id, driver_id)
    
    if success:
        print("\n✅ Ride request criado com sucesso!")
    else:
        print("\n❌ Falha ao criar ride request")
        
        # 4. Testar validação Pydantic
        test_pydantic_validation()
    
    # 5. Verificar ride requests existentes
    print(f"\n--- Verificando ride requests existentes ---")
    try:
        response = requests.get(f"{BASE_URL}/api/ride-requests?user_id={enterprise_id}")
        print(f"GET /api/ride-requests?user_id={enterprise_id}: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            requests_list = data.get('data', {}).get('ride_requests', [])
            print(f"Ride requests encontrados: {len(requests_list)}")
            for req in requests_list:
                print(f"  - {req.get('id', 'N/A')}: {req.get('status', 'N/A')}")
        else:
            print(f"Erro: {response.text}")
            
    except Exception as e:
        print(f"Erro ao verificar ride requests: {e}")

if __name__ == "__main__":
    main()