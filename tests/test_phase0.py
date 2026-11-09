"""Automated test suite for ARTH Phase 0: Foundation.
Verifies config loading, error resilience, Ollama health checks, and readiness reporting.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from arth.config import ArthConfig, BrainConfig, load_config
from arth.brain import OllamaManager
import main


class TestConfig:
    def test_load_config_defaults(self):
        """Verify load_config loads valid defaults matching ARTH_SPEC."""
        config = load_config()

        # Brain checks (Sections 1, 22)
        assert config.brain.model == "gemma4:12b"
        assert config.brain.fallback_model == "gemma4:e4b"
        assert config.brain.context_window > 2048
        assert config.brain.context_window == 8192

        # User persona (Sections 8, 32)
        assert config.user.name == "Boss"

        # Voice & Languages (Section 2)
        assert config.voice.wake_word == "ARTH"
        assert "en" in config.voice.languages
        assert "hi" in config.voice.languages
        assert "kn" in config.voice.languages

        # Quiet hours (Section 15)
        assert config.quiet_hours.enabled is True
        assert config.quiet_hours.start == "22:00"
        assert config.quiet_hours.end == "07:00"

        # File bounds (Section 4)
        assert "ARTH_Workspace" in config.files.allowed_folder

    def test_load_config_missing_file_resilience(self, tmp_path):
        """Verify that a missing config file falls back gracefully without crashing."""
        nonexistent = tmp_path / "does_not_exist.yaml"
        config = load_config(config_path=nonexistent)
        assert config.user.name == "Boss"
        assert config.brain.model == "gemma4:12b"

    def test_load_config_corrupted_file_resilience(self, tmp_path):
        """Verify that corrupted YAML falls back gracefully without crashing."""
        corrupt_file = tmp_path / "corrupt.yaml"
        corrupt_file.write_text(":::not valid yaml::: [[{{", encoding="utf-8")
        config = load_config(config_path=corrupt_file)
        assert config.user.name == "Boss"
        assert config.brain.model == "gemma4:12b"


class TestBrain:
    def test_ollama_manager_mock_transport_readiness(self):
        """Test OllamaManager against mock HTTP response verifying status parsing."""
        cfg = ArthConfig()
        cfg.brain.auto_start = False

        manager = OllamaManager(cfg)

        mock_payload = {
            "models": [
                {"name": "gemma4:12b", "model": "gemma4:12b"},
                {"name": "gemma4:e4b", "model": "gemma4:e4b"},
            ]
        }
        mock_resp = httpx.Response(200, json=mock_payload)

        with patch("httpx.get", return_value=mock_resp):
            status = manager.verify_readiness()

            assert status["ready"] is True
            assert status["running"] is True
            assert status["message"] == "Ollama is ready"
            assert status["model_available"] is True
            assert "gemma4:12b" in status["models"]

    def test_ollama_manager_fallback_model_selection(self):
        """Test OllamaManager detects fallback model if primary is absent."""
        cfg = ArthConfig()
        cfg.brain.auto_start = False

        manager = OllamaManager(cfg)

        mock_payload = {
            "models": [
                {"name": "gemma4:e4b", "model": "gemma4:e4b"},
            ]
        }
        mock_resp = httpx.Response(200, json=mock_payload)

        with patch("httpx.get", return_value=mock_resp):
            status = manager.verify_readiness()

            assert status["ready"] is True
            assert status["running"] is True
            assert status["message"] == "Ollama is ready"
            assert status["active_model"] == "gemma4:e4b"

    def test_ollama_manager_when_offline(self):
        """Test OllamaManager handling an offline endpoint without crashing."""
        cfg = ArthConfig()
        cfg.brain.ollama_host = "http://127.0.0.1:59999"
        cfg.brain.auto_start = False

        manager = OllamaManager(cfg)

        with patch("httpx.get", side_effect=httpx.ConnectError("Connection refused")):
            status = manager.verify_readiness()

            assert status["ready"] is False
            assert status["running"] is False
            assert "Boss, Ollama is not running" in status["message"]

    def test_context_window_options(self):
        """Test context window option exceeds the 2048 default."""
        cfg = ArthConfig()
        cfg.brain.context_window = 16384
        manager = OllamaManager(cfg)

        opts = manager.get_generation_options()
        assert opts["num_ctx"] == 16384
        assert opts["num_ctx"] > 2048


class TestMainCLI:
    def test_main_cli_prints_ollama_is_ready(self, capsys):
        """Test main() prints 'Ollama is ready' when Ollama status is verified."""
        mock_status = {
            "ready": True,
            "running": True,
            "model_available": True,
            "message": "Ollama is ready",
            "detail": "Model 'gemma4:12b' is available.",
        }

        with patch("arth.brain.OllamaManager.verify_readiness", return_value=mock_status):
            with patch("sys.argv", ["main.py"]):
                exit_code = main.main()
                assert exit_code == 0

        captured = capsys.readouterr()
        assert "Loaded configuration for Boss." in captured.out
        assert "Configured brain: gemma4:12b" in captured.out
        assert "Ollama is ready" in captured.out

    def test_main_cli_reports_unready_gracefully(self, capsys):
        """Test main() prints plain message when Ollama is offline without crashing."""
        mock_status = {
            "ready": False,
            "running": False,
            "message": "Boss, Ollama is not running and I couldn't start it automatically.",
        }

        with patch("arth.brain.OllamaManager.verify_readiness", return_value=mock_status):
            with patch("sys.argv", ["main.py"]):
                exit_code = main.main()
                assert exit_code == 1

        captured = capsys.readouterr()
        assert "Boss, Ollama is not running" in captured.out
