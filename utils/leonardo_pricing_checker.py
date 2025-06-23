import requests
import json
import os
from pathlib import Path

def get_leonardo_pricing(api_key, image_width=1472, image_height=832, num_images=1, is_ultra=False, alchemy_mode=True):
    """
    Obtiene información de precios de Leonardo.ai usando su API de calculador de precios
    """
    url = "https://cloud.leonardo.ai/api/rest/v1/pricing-calculator"
    
    headers = {
        'accept': 'application/json',
        'authorization': f'Bearer {api_key}',
        'content-type': 'application/json'
    }
    
    # Configuración para Phoenix model con los parámetros que usamos
    payload = {
        "serviceParams": {
            "IMAGE_GENERATION": {
                "isUltra": is_ultra,
                "imageHeight": image_height,
                "imageWidth": image_width,
                "numImages": num_images,
                "inferenceSteps": 10,
                "promptMagic": False,
                "alchemyMode": alchemy_mode,
                "highResolution": False,
                "isModelCustom": False,
                "isSDXL": False,
                "isPhoenix": True
            }
        },
        "service": "IMAGE_GENERATION"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener precios: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Código de error: {e.response.status_code}")
            print(f"Respuesta: {e.response.text}")
        return None

def check_account_balance(api_key):
    """
    Verifica el saldo de la cuenta de Leonardo.ai
    """
    url = "https://cloud.leonardo.ai/api/rest/v1/users/me"
    
    headers = {
        'accept': 'application/json',
        'authorization': f'Bearer {api_key}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error al verificar saldo: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Código de error: {e.response.status_code}")
            print(f"Respuesta: {e.response.text}")
        return None

def main():
    # Cargar API key desde el archivo
    api_key_path = Path("config/credentials/leonardo_api_key.txt")
    
    if not api_key_path.exists():
        print("❌ No se encontró el archivo de API key de Leonardo.ai")
        print("Por favor, crea el archivo: config/credentials/leonardo_api_key.txt")
        return
    
    with open(api_key_path, 'r') as f:
        api_key = f.read().strip()
    
    print("🔍 Verificando información de precios y saldo de Leonardo.ai...")
    print("=" * 60)
    
    # Verificar saldo de la cuenta
    print("\n📊 INFORMACIÓN DE LA CUENTA:")
    account_info = check_account_balance(api_key)
    if account_info:
        print(f"✅ Información de cuenta obtenida")
        if 'subscription' in account_info:
            sub = account_info['subscription']
            print(f"   Plan: {sub.get('plan', 'N/A')}")
            print(f"   Estado: {sub.get('status', 'N/A')}")
        if 'api_credits' in account_info:
            credits = account_info['api_credits']
            print(f"   Créditos disponibles: {credits}")
    else:
        print("❌ No se pudo obtener información de la cuenta")
    
    # Verificar precios para diferentes configuraciones
    print("\n💰 CALCULADOR DE PRECIOS:")
    
    # Configuración 1: Modo Quality (alchemy=true, ultra=false)
    print("\n1️⃣ Configuración Quality (Alchemy ON, Ultra OFF):")
    pricing_quality = get_leonardo_pricing(
        api_key, 
        image_width=1472, 
        image_height=832, 
        num_images=1, 
        is_ultra=False, 
        alchemy_mode=True
    )
    
    if pricing_quality:
        print(f"   ✅ Precio calculado: {pricing_quality}")
        if 'apiCreditCost' in pricing_quality:
            print(f"   Costo en créditos: {pricing_quality['apiCreditCost']}")
    else:
        print("   ❌ No se pudo calcular el precio")
    
    # Configuración 2: Modo Ultra (alchemy=true, ultra=true)
    print("\n2️⃣ Configuración Ultra (Alchemy ON, Ultra ON):")
    pricing_ultra = get_leonardo_pricing(
        api_key, 
        image_width=1472, 
        image_height=832, 
        num_images=1, 
        is_ultra=True, 
        alchemy_mode=True
    )
    
    if pricing_ultra:
        print(f"   ✅ Precio calculado: {pricing_ultra}")
        if 'apiCreditCost' in pricing_ultra:
            print(f"   Costo en créditos: {pricing_ultra['apiCreditCost']}")
    else:
        print("   ❌ No se pudo calcular el precio")
    
    # Configuración 3: Modo Fast (alchemy=false, ultra=false)
    print("\n3️⃣ Configuración Fast (Alchemy OFF, Ultra OFF):")
    pricing_fast = get_leonardo_pricing(
        api_key, 
        image_width=1472, 
        image_height=832, 
        num_images=1, 
        is_ultra=False, 
        alchemy_mode=False
    )
    
    if pricing_fast:
        print(f"   ✅ Precio calculado: {pricing_fast}")
        if 'apiCreditCost' in pricing_fast:
            print(f"   Costo en créditos: {pricing_fast['apiCreditCost']}")
    else:
        print("   ❌ No se pudo calcular el precio")
    
    # Calcular costo para un video completo (19 imágenes)
    print("\n🎬 COSTO PARA UN VIDEO COMPLETO (19 imágenes):")
    if pricing_quality and 'apiCreditCost' in pricing_quality:
        costo_por_imagen = pricing_quality['apiCreditCost']
        costo_total = costo_por_imagen * 19
        print(f"   Costo por imagen: {costo_por_imagen} créditos")
        print(f"   Costo total (19 imágenes): {costo_total} créditos")
        
        # Estimación en USD (aproximado)
        # Nota: Esta es una estimación, los precios reales pueden variar
        print(f"   Estimación USD (aproximado): ${costo_total * 0.015:.2f}")

if __name__ == "__main__":
    main() 