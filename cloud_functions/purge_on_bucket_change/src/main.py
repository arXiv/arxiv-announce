import re
from typing import Optional, List
import os

import functions_framework
from cloudevents.http import CloudEvent
from google.api_core import retry

from arxiv.identifier import Identifier, STANDARD as MODERN_ID, _archive, _category
from arxiv.integration.fastly.purge import purge_fastly_keys

#logging configuration
if not(os.environ.get('LOG_LOCALLY')):
    import google.cloud.logging
    client = google.cloud.logging.Client()
    client.setup_logging()
import logging 
log_level_str = os.getenv('LOG_LEVEL', 'INFO')
log_level = getattr(logging, log_level_str.upper(), logging.INFO)
logging.basicConfig(level=log_level)

PS_CACHE_OLD_ID = re.compile(r'(%s)\/[^\/]*\/\d*\/(\d{2}[01]\d{4}(v\d*)?)' % f'{_archive}|{_category}')
"EX /ps_cache/hep-ph/pdf/0511/0511005v2.pdf"

FILES_TO_IGNORE=['outcome.tar.gz','LaTeXML.cache','__stdout.txt']

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
    def __init__(self, always_soft_purge: bool=False, dry_run: bool=False) -> None:
        self.always_soft_purge = always_soft_purge
        self.dry_run = dry_run

    @retry.Retry()
    def invalidate(self, keys: List[str], soft_purge: bool=False) -> None:
        if self.dry_run:
            logging.info(f"DRY_RUN: Would have purged keys: {keys} soft purge: {soft_purge}")
            return

        purge_fastly_keys(keys, soft_purge=(self.always_soft_purge or soft_purge))


def invalidate_for_gs_change(bucket: str, key: str, invalidator: Invalidator) -> None:
    if any(ignored in key for ignored in FILES_TO_IGNORE):
        logging.debug(f"No purge for ignored file type: gs://{bucket}/{key}")
        return

    if '/html/' in key: #native html files
        path="html"
    elif key.endswith('.pdf'): #processed pdfs, as well as source pdfs 
        path="pdf"
    else:
        logging.debug(f"No purge: gs://{bucket}/{key} not an html or pdf path")
        return
    
    paper_id = _paperid(key)
    if not paper_id:
        logging.debug(f"No purge: gs://{bucket}/{key} not related to an arxiv paper id")
        return
     
    purge_keys=[f'{path}-{paper_id.id}-current', f'{path}-{paper_id.idv}'] #always purge current just to be sure
    logging.info(f"attempting purge keys: {purge_keys} for location: {key} in bucket: {bucket}")
   
    try:
        invalidator.invalidate(purge_keys)
    except Exception as exc:
        logging.error(f"Purge failed: {purge_keys} failed {exc}")


@functions_framework.cloud_event
def main(cloud_event: CloudEvent) -> None:
    try:
        data = cloud_event.get_data()
        bucket=data.get("bucket")
        name=data.get("name")
        if bucket is None or name is None:
            logging.error(f"bad message data format. bucket: {bucket}, name: {name}, message data: {data}")
            return #dont retry

        invalidate_for_gs_change(bucket,
                                 name,
                                 Invalidator(os.environ.get('ALWAYS_SOFT_PURGE', "0") == "1",
                                             os.environ.get("DRY_RUN", "0") == "1"))
    except Exception as ex:
        logging.error(cloud_event)
        raise ex
