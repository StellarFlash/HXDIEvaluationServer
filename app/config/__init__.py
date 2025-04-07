from .config import Config

def get_config():
    return Config()

__all__ = ['get_config']
