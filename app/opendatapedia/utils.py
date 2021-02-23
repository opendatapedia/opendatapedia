from pathlib        import Path, PurePath
from requests       import get
from urllib.parse   import urlparse

import unidecode

from opendatapedia.config   import logger

def pretty_url(url: str):
    pretty_url = unidecode.unidecode(url).replace(' ', '_').replace('\'', '_').lower()

    return pretty_url


def save_url_to_directory(url: str, directory: str, downloaded_file=None, force=False) -> str:
    path = None
    if downloaded_file:
        path = f"{directory}/{downloaded_file}"
    else:
        a = urlparse(url)
        filename = PurePath(a.path).name
        path = f"{directory}/{filename}"
    if not Path(path).is_file() and not force:
        logger.info(f"Downloading '{url}' to '{path}'...")
        response = get(url)
        Path(directory).mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(response.content)
    else:
        logger.info(f"No download of '{url}' because '{path}' already exists")

    return path