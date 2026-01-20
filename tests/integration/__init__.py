"""Integration tests for The Mixer.

These tests validate end-to-end workflows and require:
- Real audio files or YouTube access
- All dependencies installed (Whisper, Demucs, etc.)
- LLM API keys configured
- Sufficient disk space and processing power

Run integration tests with:
    pytest tests/integration/ -v -m integration

Skip slow tests:
    pytest tests/integration/ -v -m "integration and not skip"
"""
