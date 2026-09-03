#!/usr/bin/env python3
"""
Integration Helper - Einfache Integration in alle Projekte
"""

import os
import sys
import json
from gateway import AIModelGateway
import asyncio

class ProjectIntegrator:
    def __init__(self, gateway: AIModelGateway):
        self.gateway = gateway
    
    def inject_into_project(self, project_path: str):
        """Injiziere die Gateway-Integration in ein existierendes Projekt"""
        print(f"📦 Injiziere Gateway in {project_path}...")
        
        # Erstelle .env Template
        env_template = """# AI Model Gateway - Konfiguration
ANTHROPIC_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here
REPLICATE_API_KEY=your_key_here
TOGETHER_API_KEY=your_key_here
"""
        env_path = os.path.join(project_path, ".env.gateway")
        with open(env_path, 'w') as f:
            f.write(env_template)
        print(f"✅ .env Template erstellt: {env_path}")
        
        # Erstelle Integrations-Wrapper
        wrapper_code = '''#!/usr/bin/env python3
"""Auto-Generated Gateway Integration Wrapper"""

import sys
import os
from pathlib import Path

# Add gateway to path
gateway_path = Path(__file__).parent / "ai_gateway"
sys.path.insert(0, str(gateway_path))

from gateway import AIModelGateway
import asyncio

# Globale Gateway-Instanz
_gateway = None

def get_gateway():
    global _gateway
    if _gateway is None:
        config_path = Path(__file__).parent / "ai_gateway" / "config.json"
        _gateway = AIModelGateway(str(config_path))
    return _gateway

async def query_ai(prompt, use_chain=False, chain=None):
    """
    Einfache Funktion zum Abfragen der KI-Modelle
    
    Args:
        prompt: Die Eingabeaufforderung
        use_chain: Verkettete Modelle nutzen
        chain: Liste der Modelle in Kette [Default: ["claude", "openrouter"]]
    
    Returns:
        str: Die KI-Antwort
    """
    gateway = get_gateway()
    
    if use_chain:
        if chain is None:
            chain = ["claude", "openrouter"]
        result = await gateway.chain_models(prompt, chain)
        return result["final_output"]
    else:
        result = await gateway.auto_route(prompt)
        return result["primary"]

def query_ai_sync(prompt, use_chain=False, chain=None):
    """Synchrone Wrapper-Funktion"""
    return asyncio.run(query_ai(prompt, use_chain, chain))

# Beispielnutzung
if __name__ == "__main__":
    result = query_ai_sync("Hallo, wer bin ich?")
    print(f"Antwort: {result}")
'''
        wrapper_path = os.path.join(project_path, "ai_gateway_wrapper.py")
        with open(wrapper_path, 'w') as f:
            f.write(wrapper_code)
        print(f"✅ Integrations-Wrapper erstellt: {wrapper_path}")

class GlobalAIRouter:
    """Globaler Router für alle Projekte"""
    
    @staticmethod
    def init_all_projects(projects_dir: str):
        """Initialisiere Gateway für alle Projekte in einem Verzeichnis"""
        print(f"\n🌍 Initialisiere Gateway für alle Projekte in {projects_dir}...\n")
        
        for project_name in os.listdir(projects_dir):
            project_path = os.path.join(projects_dir, project_name)
            if os.path.isdir(project_path):
                print(f"📁 {project_name}")
                integrator = ProjectIntegrator(AIModelGateway())
                integrator.inject_into_project(project_path)
                print()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
        gateway = AIModelGateway()
        integrator = ProjectIntegrator(gateway)
        integrator.inject_into_project(project_path)
    else:
        print("Usage: python integration_helper.py <project_path>")
        print("\nOder nutze GlobalAIRouter für alle Projekte")