import os

from .environment import env

BANANAS_SECRETS_DIR_ENV_KEY = "BANANAS_SECRETS_DIR"


def get_secret(secret_name, default=None):
    """
    Gets contents of secret file

    :param secret_name: The name of the secret present in BANANAS_SECRETS_DIR
    :param default: Default value to return if no secret was found
    :return: The secret or default if not found
    """
    secrets_dir = get_secrets_dir()
    secret_path = os.path.join(secrets_dir, secret_name)
    try:
        with open(secret_path, "r") as secret_file:
            return secret_file.read()
    except OSError:
        return default


def get_secrets_dir():
    """
    Returns path to secrets directory
    """
    return env.get(BANANAS_SECRETS_DIR_ENV_KEY, "/run/secrets/")
