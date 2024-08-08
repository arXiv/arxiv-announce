
import re
from typing import Optional, List, Tuple
import os

from cloudevents.http import CloudEvent
import functions_framework
from google.api_core import retry

from arxiv.identifier import Identifier, STANDARD as MODERN_ID, _archive, _category
from arxiv.integration.fastly.purge import purge_fastly_keys


functions_framework.setup_logging()
import logging


PS_CACHE_OLD_ID = re.compile(r'(%s)\/[^\/]*\/\d*\/(\d{2}[01]\d{4}(v\d*)?)' % f'{_archive}|{_category}')
"EX /ps_cache/hep-ph/pdf/0511/0511005v2.pdf"

def _paperid(name: str) -> Optional[Identifier]:
    if not name:
        return None
    if match := MODERN_ID.search(name):
        return Identifier(match.group("arxiv_id"))
    if match := PS_CACHE_OLD_ID.search(name):
        return Identifier(match.group(1) + "/" + match.group(2))
    else:
        return None

class Invalidator:
    def __init__(self, fastly_api_token: str, always_soft_purge: bool=False, dry_run: bool=False) -> None:
        self.fastly_api_token = fastly_api_token
        self.always_soft_purge = always_soft_purge
        self.dry_run = dry_run

    @retry.Retry()
    def invalidate(self, key: str, paperid: Identifier, soft_purge: bool=False) -> None:
        if self.dry_run:
            logging.info(f"DRY_RUN: Would have requested '{key}'")
            return

        if self.always_soft_purge or soft_purge:
            purge_fastly_keys(key, soft_purge=True)
        else:
            purge_fastly_keys(key, soft_purge=False)


def invalidate_for_gs_change(bucket: str, key: str, invalidator: Invalidator) -> None:
    #find what to purge
    paper_id = _paperid(key)
    if not paper_id:
        logging.info(f"No purge: gs://{bucket}/{key} not related to an arxiv paper id")
        return
    
    if "/pdf/" in key:
        purge_key=f"pdf-{paper_id.id}"
    elif '/html/' in key:
        purge_key=f"html-{paper_id.id}"
    else:
        logging.info(f"No purge: gs://{bucket}/{key} not an html or pdf path")
        return
    
    #perform purge
    try:
        invalidator.invalidate(purge_key)
    except Exception as exc:
        logging.error(f"Purge failed: {purge_key} failed {exc}")


@functions_framework.cloud_event
def main(cloud_event: CloudEvent) -> None:
    try:
        data = cloud_event.get_data()
        invalidate_for_gs_change(data.get("bucket"),
                                 data.get("name"),
                                 Invalidator(os.environ.get("FASTLY_API_TOKEN", "NOT_CONFIGURED"),
                                             os.environ.get("FASTLY_URL", "https://api.fastly.com/purge"),
                                             os.environ.get('ALWAYS_SOFT_PURGE', "0") == "1",
                                             os.environ.get("DRY_RUN", "0") == "1"))
    except Exception as ex:
        logging.error(cloud_event)
        raise ex
