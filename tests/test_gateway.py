import asyncio
import importlib.util
import json
import os
import sys
import tempfile
import unittest

from gateway import AIModelGateway
from integration_helper import ProjectIntegrator


class AIModelGatewayTests(unittest.TestCase):
    def test_missing_default_config_uses_builtin_model_definitions(self):
        gateway = AIModelGateway(config_path="/tmp/does-not-exist-config.json")

        status = gateway.get_status()

        self.assertEqual(
            set(status),
            {"claude", "openrouter", "groq", "huggingface"},
        )
        self.assertFalse(status["claude"]["available"])
        self.assertEqual(status["openrouter"]["name"], "OpenRouter")

    def test_invalid_config_falls_back_to_builtin_model_definitions(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as invalid_config:
            invalid_config.write("{invalid json")
            invalid_config.flush()

            gateway = AIModelGateway(config_path=invalid_config.name)

        status = gateway.get_status()

        self.assertIn("claude", status)
        self.assertEqual(status["huggingface"]["name"], "Hugging Face")

    def test_config_without_models_falls_back_to_builtin_model_definitions(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as config_file:
            config_file.write("{}")
            config_file.flush()

            gateway = AIModelGateway(config_path=config_file.name)

        status = gateway.get_status()

        self.assertIn("openrouter", status)
        self.assertEqual(status["groq"]["name"], "Groq")

    def test_config_with_non_mapping_models_falls_back_to_builtin_model_definitions(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as config_file:
            config_file.write('{"models": []}')
            config_file.flush()

            gateway = AIModelGateway(config_path=config_file.name)

        status = gateway.get_status()

        self.assertIn("huggingface", status)
        self.assertEqual(status["claude"]["name"], "Claude")

    def test_directory_config_path_falls_back_to_builtin_model_definitions(self):
        with tempfile.TemporaryDirectory() as config_dir:
            gateway = AIModelGateway(config_path=config_dir)

        status = gateway.get_status()

        self.assertIn("groq", status)
        self.assertEqual(status["claude"]["name"], "Claude")

    def test_auto_route_returns_empty_result_when_no_providers_are_configured(self):
        gateway = AIModelGateway(config_path="/tmp/does-not-exist-config.json")

        result = asyncio.run(gateway.auto_route("Hallo"))

        self.assertEqual(result["prompt"], "Hallo")
        self.assertEqual(result["responses"], {})
        self.assertIsNone(result["primary"])

    def test_project_integration_creates_embedded_gateway_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = os.path.join(temp_dir, "project")
            integrator = ProjectIntegrator(AIModelGateway())

            integrator.inject_into_project(project_dir)

            self.assertTrue(os.path.isfile(os.path.join(project_dir, ".env.gateway")))
            self.assertTrue(os.path.isfile(os.path.join(project_dir, "ai_gateway_wrapper.py")))
            self.assertTrue(os.path.isfile(os.path.join(project_dir, "ai_gateway", "gateway.py")))
            self.assertTrue(os.path.isfile(os.path.join(project_dir, "ai_gateway", "config.json")))
            self.assertTrue(os.path.isfile(os.path.join(project_dir, "ai_gateway", "requirements.txt")))

            with open(os.path.join(project_dir, "ai_gateway", "config.json"), encoding="utf-8") as f:
                config = json.load(f)

            self.assertIn("models", config)
            self.assertIn("claude", config["models"])

    def test_project_integration_env_template_only_lists_supported_keys(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = os.path.join(temp_dir, "project")
            integrator = ProjectIntegrator(AIModelGateway())

            integrator.inject_into_project(project_dir)

            with open(os.path.join(project_dir, ".env.gateway"), encoding="utf-8") as f:
                env_template = f.read()

            self.assertIn("ANTHROPIC_API_KEY=your_key_here", env_template)
            self.assertIn("OPENROUTER_API_KEY=your_key_here", env_template)
            self.assertNotIn("REPLICATE_API_KEY", env_template)
            self.assertNotIn("TOGETHER_API_KEY", env_template)

    def test_generated_wrapper_loads_embedded_gateway(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = os.path.join(temp_dir, "project")
            integrator = ProjectIntegrator(AIModelGateway())

            integrator.inject_into_project(project_dir)

            wrapper_path = os.path.join(project_dir, "ai_gateway_wrapper.py")
            spec = importlib.util.spec_from_file_location("generated_ai_gateway_wrapper", wrapper_path)
            module = importlib.util.module_from_spec(spec)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)

            original_sys_path = sys.path[:]
            try:
                sys.path.insert(0, project_dir)
                spec.loader.exec_module(module)
                self.assertIsNone(module.query_ai_sync("Hallo"))
            finally:
                sys.path[:] = original_sys_path


if __name__ == "__main__":
    unittest.main()
