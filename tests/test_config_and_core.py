def test_settings_loads():
    """Settings deve carregar sem erros e ter valores padrão corretos."""
    from src.config.settings import settings

    assert settings.openai_model == "gpt-4o-mini"
    assert settings.rag_chunk_size == 1000
    assert settings.rag_top_k == 4


def test_settings_singleton():
    """Importar settings duas vezes deve retornar o mesmo objeto."""
    from src.config.settings import settings as s1
    from src.config.settings import settings as s2

    assert s1 is s2


def test_get_logger_returns_logger():
    """get_logger deve retornar um logger usável."""
    from src.core.logging import get_logger

    logger = get_logger("test")
    assert logger is not None
    logger.info("test.smoke_ok")


def test_setup_loggin_does_not_raise():
    """setup_logging não deve lançar exceção."""
    from src.core.logging import setup_logging

    setup_logging("INFO")
    setup_logging("DEBUG")


def test_checkpointer_returns_memory_saver_in_testing(monkeypatch):
    """Em APP_ENV=testing deve retornar MemorySaver."""
    from langgraph.checkpoint.memory import MemorySaver

    monkeypatch.setenv("APP_ENV", "testing")

    import importlib

    import src.config.settings as settings_module

    importlib.reload(settings_module)
    import src.core.checkpointer as cp_module

    importlib.reload(cp_module)

    with cp_module.checkpointer_context() as checkpointer:
        assert isinstance(checkpointer, MemorySaver)
