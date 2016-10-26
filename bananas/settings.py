import bananas.environment


ENV_SETTINGS = bananas.environment.get_settings()

__all__ = list(ENV_SETTINGS)

locals().update(ENV_SETTINGS)
