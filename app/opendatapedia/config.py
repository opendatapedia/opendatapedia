from loguru import logger
import sys

CONFIG_DIR = "../conf"
CONFIG_DATASETS_FILE = f"{CONFIG_DIR}/datasets.yml"
CONFIG_ODP_DATASETS_FILE = f"{CONFIG_DIR}/odp_datasets.yml"
CONFIG_PAGES_FILE = f"{CONFIG_DIR}/pages.yml"
CONFIG_ODP_PAGES_FILE = f"{CONFIG_DIR}/odp_pages.yml"

DATA_DIR = "../data"

PUBLIC_DIR = "../../opendatapedia.github.io/docs"
PUBLIC_DATA_DIR = f"{PUBLIC_DIR}/data"

TEMPLATES_DIR = "../templates"
TEMPLATES_GENERIC_DIR = f"{TEMPLATES_DIR}/generic"

log_config = {
    "handlers" : [
        { "sink": sys.stdout, "colorize": True, "format": "<green>{time}</green> <lvl>[{level}] {message}</lvl>"}
    ],
    "extra": {"app": "OpenDataPedia"}
}
logger.configure(**log_config)
