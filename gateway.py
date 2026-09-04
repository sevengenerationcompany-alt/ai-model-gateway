#!/usr/bin/env python3
"""
AI Model Gateway - Automatische Integration aller KI-Modelle mit Claude
"""

import json
import asyncio
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import httpx
except ImportError:
    httpx = None


DEFAULT_CONFIG = {
    "models": {
        "claude": {
            "provider": "anthropic",
            "name": "Claude",
            "models": ["claude-3-5-sonnet-20241022"],
            "priority": 1,
            "apiKeyEnv": "ANTHROPIC_API_KEY",
        },
        "openrouter": {
            "provider": "openrouter",
            "name": "OpenRouter",
            "models": ["mistralai/mistral-7b-instruct:free"],
            "priority": 2,
            "apiKeyEnv": "OPENROUTER_API_KEY",
        },
        "groq": {
            "provider": "groq",
            "name": "Groq",
            "models": ["mixtral-8x7b-32768"],
            "priority": 3,
            "apiKeyEnv": "GROQ_API_KEY",
        },
        "huggingface": {
            "provider": "huggingface",
            "name": "Hugging Face",
            "models": ["mistralai/Mistral-7B-Instruct-v0.1"],
            "priority": 4,
            "apiKeyEnv": "HUGGINGFACE_API_KEY",
        },
    }
}


@dataclass
class ModelConfig:
    provider: str
    name: str
    models: List[str]
    priority: int
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class AIModelGateway:
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.claude_client = None
        if anthropic is not None and anthropic_api_key:
            self.claude_client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.models = self._load_models()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return DEFAULT_CONFIG

    def _load_models(self) -> Dict[str, ModelConfig]:
        """Lade alle verfügbaren Modelle aus der Konfiguration"""
        models = {}
        for provider, config in self.config["models"].items():
            api_key = os.getenv(config.get("apiKeyEnv"))
            models[provider] = ModelConfig(
                provider=config["provider"],
                name=config["name"],
                models=config["models"],
                priority=config["priority"],
                api_key=api_key,
                base_url=config.get("baseUrl")
            )
        return models

    async def query_claude(self, prompt: str, model: str = "claude-3-5-sonnet-20241022") -> str:
        """Frage Claude mit automatischem Fallback ab"""
        if self.claude_client is None:
            return None
        try:
            message = self.claude_client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Claude error: {e}")
            return None

    async def query_openrouter(self, prompt: str, model: str = "mistralai/mistral-7b-instruct:free") -> str:
        """Frage OpenRouter ab"""
        config = self.models.get("openrouter")
        if httpx is None or config is None or not config.api_key:
            return None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"******",
                        "HTTP-Referer": "https://github.com/sevengenerationcompany-alt/ai-model-gateway"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1024
                    }
                )
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"OpenRouter error: {e}")
            return None

    async def query_groq(self, prompt: str, model: str = "mixtral-8x7b-32768") -> str:
        """Frage Groq ab"""
        config = self.models.get("groq")
        if httpx is None or config is None or not config.api_key:
            return None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"******",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1024
                    }
                )
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Groq error: {e}")
            return None

    async def query_huggingface(self, prompt: str, model: str = "mistralai/Mistral-7B-Instruct-v0.1") -> str:
        """Frage Hugging Face ab"""
        config = self.models.get("huggingface")
        if httpx is None or config is None or not config.api_key:
            return None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers={"Authorization": f"******"},
                    json={"inputs": prompt}
                )
                return response.json()[0]["generated_text"]
        except Exception as e:
            print(f"Hugging Face error: {e}")
            return None

    async def auto_route(self, prompt: str, task_type: str = "general") -> Dict[str, Any]:
        """
        Automatisches Routing zu den besten Modellen basierend auf Aufgabentyp
        """
        results = {}
        tasks = []

        # Starte Claude als primäres Modell
        if self.models.get('claude') and self.models['claude'].api_key:
            tasks.append(("claude", self.query_claude(prompt)))

        # Fallback zu OpenRouter
        if self.models.get('openrouter') and self.models['openrouter'].api_key:
            tasks.append(("openrouter", self.query_openrouter(prompt)))

        # Fallback zu Groq
        if self.models.get('groq') and self.models['groq'].api_key:
            tasks.append(("groq", self.query_groq(prompt)))

        # Fallback zu Hugging Face
        if self.models.get('huggingface') and self.models['huggingface'].api_key:
            tasks.append(("huggingface", self.query_huggingface(prompt)))

        # Führe alle Anfragen parallel aus
        if tasks:
            responses = await asyncio.gather(
                *[task[1] for task in tasks],
                return_exceptions=True
            )

            for (provider, _), response in zip(tasks, responses):
                if response and not isinstance(response, Exception):
                    results[provider] = response

        return {
            "prompt": prompt,
            "responses": results,
            "primary": results.get("claude") or next(iter(results.values()), None)
        }

    async def chain_models(self, prompt: str, chain: List[str]) -> Dict[str, Any]:
        """
        Verkette mehrere Modelle: Output eines Modells wird Input des nächsten
        """
        result = prompt
        chain_results = {}

        for model_provider in chain:
            if model_provider == "claude":
                result = await self.query_claude(result)
            elif model_provider == "openrouter":
                result = await self.query_openrouter(result)
            elif model_provider == "groq":
                result = await self.query_groq(result)
            elif model_provider == "huggingface":
                result = await self.query_huggingface(result)

            chain_results[model_provider] = result

        return {
            "original_prompt": prompt,
            "chain": chain,
            "results": chain_results,
            "final_output": result
        }

    def get_status(self) -> Dict[str, Any]:
        """Gebe Status aller verfügbaren Modelle"""
        status = {}
        for provider, model in self.models.items():
            status[provider] = {
                "name": model.name,
                "available": model.api_key is not None,
                "priority": model.priority,
                "models": model.models
            }
        return status


async def main():
    gateway = AIModelGateway()

    print("🤖 AI Model Gateway - Status")
    print("=" * 50)
    for provider, status in gateway.get_status().items():
        print(f"{status['name']}: {'✅ Available' if status['available'] else '❌ Not configured'}")

    print("\n📝 Test-Anfrage...")
    print("=" * 50)

    test_prompt = "Was ist künstliche Intelligenz? Antworte kurz in 2 Sätzen."

    # Auto-Routing Test
    result = await gateway.auto_route(test_prompt)
    print(f"\n🔄 Auto-Routing Ergebnis:")
    print(f"Primäre Antwort:\n{result['primary']}\n")

    # Model-Chain Test
    print("\n⛓️ Model-Chain Test:")
    chain_result = await gateway.chain_models(
        "Schreibe einen Haiku über KI",
        ["claude", "openrouter"]
    )
    print(f"Final Output:\n{chain_result['final_output']}")


if __name__ == "__main__":
    asyncio.run(main())
