def drf_installed() -> bool:
    try:
        import rest_framework

        return True
    except ModuleNotFoundError:
        return False
