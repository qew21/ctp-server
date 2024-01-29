import os

from dynaconf import Dynaconf
import logging.config
import yaml


account = Dynaconf(envvar_prefix="CTP", load_dotenv=True, environments=True, settings_files=["account.yaml"])


if os.path.exists("logging.yaml"):
    with open("logging.yaml", "r") as f:
        log_cfg = yaml.safe_load(f.read())
        logging.config.dictConfig(log_cfg)


logger = logging.getLogger(__name__)

