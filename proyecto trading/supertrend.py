import requests
import pandas as pd
import numpy as np

# Configuración de la API de Capital.com
API_URL = "https://api-capital.backend-capital.com"
API_KEY = "f5AG8vXXwcETKqLi"  # Inserta tu API Key de Capital.com aquí

# Parámetros para la estrategia Supertrend
ATR_PERIOD = 10
SUPER_MULTIPLIER = 3
TAKE_PROFIT_PIPS = 7

def obtener_datos_mercado(epic, intervalo):
    """Obtiene los datos del mercado desde Capital.com"""
    url = f"{API_URL}/history/candles/{epic}?resolution={intervalo}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Error al obtener datos de mercado: {response.status_code}, {response.text}")
    
    data = response.json()
    df = pd.DataFrame(data['candles'], columns=["timestamp", "open", "high", "low", "close"])
    return df

def calcular_supertrend(df, atr_period, multiplier):
    """Calcula el indicador Supertrend."""
    df['HL2'] = (df['high'] + df['low']) / 2
    df['ATR'] = df['high'] - df['low']
    df['BasicUpperband'] = df['HL2'] + (multiplier * df['ATR'])
    df['BasicLowerband'] = df['HL2'] - (multiplier * df['ATR'])
    df['FinalUpperband'] = df['BasicUpperband']
    df['FinalLowerband'] = df['BasicLowerband']

    df['Supertrend'] = 0
    for i in range(1, len(df)):
        if df['close'][i] > df['FinalUpperband'][i-1]:
            df['Supertrend'][i] = df['FinalLowerband'][i]
        elif df['close'][i] < df['FinalLowerband'][i-1]:
            df['Supertrend'][i] = df['FinalUpperband'][i]
        else:
            df['Supertrend'][i] = df['Supertrend'][i-1]

    return df

def realizar_orden(epic, direccion, size, take_profit_pips):
    """Realiza una orden de compra o venta en Capital.com"""
    url = f"{API_URL}/trading/orders"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    order = {
        "epic": epic,
        "direction": direccion,
        "size": size,
        "takeProfitDistance": take_profit_pips / 10  # Ajuste de pips a unidades del mercado
    }
    response = requests.post(url, json=order, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Error al ejecutar la orden: {response.status_code}, {response.text}")
    
    return response.json()

# Ejemplo de uso:
epic = "XAUUSD"  # Reemplaza con el código del activo que quieras operar
intervalo = "5MIN"  # Intervalo de tiempo para los datos (puede ser "1MIN", "5MIN", etc.)
df = obtener_datos_mercado(epic, intervalo)

# Cálculo del Supertrend
df = calcular_supertrend(df, ATR_PERIOD, SUPER_MULTIPLIER)

# Verificar si hay señal de compra o venta
ultima_fila = df.iloc[-1]
penultima_fila = df.iloc[-2]

if penultima_fila['close'] < penultima_fila['Supertrend'] and ultima_fila['close'] > ultima_fila['Supertrend']:
    print("Señal de Compra - Ejecutando orden...")
    realizar_orden(epic, "BUY", 1, TAKE_PROFIT_PIPS)
elif penultima_fila['close'] > penultima_fila['Supertrend'] and ultima_fila['close'] < ultima_fila['Supertrend']:
    print("Señal de Venta - Ejecutando orden...")
    realizar_orden(epic, "SELL", 1, TAKE_PROFIT_PIPS)
else:
    print("No hay señales de compra o venta.")
