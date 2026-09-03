#!/usr/bin/env python3
"""
Grundlegende Beispiele für die Nutzung des AI Model Gateway
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from gateway import AIModelGateway
import asyncio

async def example_1_auto_routing():
    """Beispiel 1: Automatisches Routing"""
    print("\n=== Beispiel 1: Auto-Routing ===")
    gateway = AIModelGateway()
    
    prompt = "Erkläre Machine Learning in 2 Sätzen"
    result = await gateway.auto_route(prompt)
    
    print(f"Prompt: {prompt}")
    print(f"\nPrimäre Antwort:\n{result['primary']}")
    print(f"\nVerfügbare Modelle: {list(result['responses'].keys())}")

async def example_2_model_chaining():
    """Beispiel 2: Model Chaining"""
    print("\n=== Beispiel 2: Model Chaining ===")
    gateway = AIModelGateway()
    
    # Claude schreibt zuerst, dann verfeinert OpenRouter
    prompt = "Schreibe einen Haiku über Technologie"
    result = await gateway.chain_models(prompt, ["claude", "openrouter"])
    
    print(f"Prompt: {prompt}")
    print(f"\nSchritt 1 (Claude):\n{result['results'].get('claude', 'N/A')}")
    print(f"\nSchritt 2 (OpenRouter):\n{result['results'].get('openrouter', 'N/A')}")

async def example_3_individual_models():
    """Beispiel 3: Einzelne Modelle nutzen"""
    print("\n=== Beispiel 3: Einzelne Modelle ===")
    gateway = AIModelGateway()
    
    prompt = "Was ist eine API?"
    
    # Nur Claude
    claude_response = await gateway.query_claude(prompt)
    print(f"Claude: {claude_response}\n")
    
    # Nur OpenRouter
    openrouter_response = await gateway.query_openrouter(prompt)
    print(f"OpenRouter: {openrouter_response}\n")

async def example_4_model_status():
    """Beispiel 4: Model Status"""
    print("\n=== Beispiel 4: Model Status ===")
    gateway = AIModelGateway()
    
    status = gateway.get_status()
    print("Verfügbare Modelle:\n")
    for provider, info in status.items():
        print(f"✅ {info['name']}" if info['available'] else f"❌ {info['name']}")
        print(f"   Modelle: {', '.join(info['models'][:2])}...")
        print(f"   Priorität: {info['priority']}\n")

async def example_5_error_handling():
    """Beispiel 5: Error Handling"""
    print("\n=== Beispiel 5: Error Handling ===")
    gateway = AIModelGateway()
    
    prompt = "Test Fehlerbehebung"
    result = await gateway.auto_route(prompt)
    
    # Fallback wenn primäre Antwort leer
    response = result['primary']
    if not response:
        print("Primäres Modell fehlgeschlagen, nutze Fallback...")
        response = next(iter(result['responses'].values()), "Keine Antwort verfügbar")
    
    print(f"Finale Antwort: {response}")

async def main():
    """Führe alle Beispiele aus"""
    print("🤖 AI Model Gateway - Beispiele")
    print("=" * 50)
    
    try:
        await example_1_auto_routing()
        await example_2_model_chaining()
        await example_3_individual_models()
        await example_4_model_status()
        await example_5_error_handling()
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        print("\nStelle sicher, dass:")
        print("1. Die config.json existiert")
        print("2. Die .env Datei mit API-Keys konfiguriert ist")
        print("3. Die Dependencies installiert sind (pip install -r requirements.txt)")

if __name__ == "__main__":
    asyncio.run(main())