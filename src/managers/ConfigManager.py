import toml
import os

HOME = os.path.expanduser("~")
XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME") or os.path.join(HOME, ".config")
USER_PROFILE_PATH = os.path.join(XDG_CONFIG_HOME, "pardus-domain-joiner.toml")

DEFAULT_TOML_CONTENT = """
domain = ""
username = ""
organizational_unit = ""
connection_type = "sssd"
"""


def read_config():
    try:
        return toml.load(USER_PROFILE_PATH)
    except Exception:
        return toml.loads(DEFAULT_TOML_CONTENT)


def save_config(config):
    with open(USER_PROFILE_PATH, "w") as f:
        toml.dump(config, f)
