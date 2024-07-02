"""Listens an listen to bucket change events and will purge at fastly based on
the object changed in the bucket.

Env vars:

- FASTLY_API_TOKEN required, configure from secrets
- FASTLY_URL optional, default is correct for fastly
- ALWAYS_SOFT_PURGE optional, defaults off 1 or 0
- DRY_RUN optional, defaults to off, 1 or 0

Deploy with something like:

  SA=fastly-invalidator@arxiv-production.iam.gserviceaccount.com
  # needs access to secret fastly-purge-token

  # default compute SA
  TRIGGER_SA=1090350072932-compute@developer.gserviceaccount.com

  gcloud functions deploy purge_on_obj_change \
   --retry --gen2 \
   --source ./ \
   --runtime python311  \
   --region us-central1 \
   --trigger-bucket arxiv-production-data \
   --trigger-location us \
   --trigger-service-account=$TRIGGER_SA \
   --entry-point main \
   --service-account $SA \
   --set-secrets "FASTLY_API_TOKEN=fastly-purge-token:latest" \
   --allow-unauthenticated

"""
import re
from typing import Optional, List, Tuple
import os

from cloudevents.http import CloudEvent

import functions_framework

import requests
from arxiv.identifier import Identifier, STANDARD as MODERN_ID, _archive, _category
from google.api_core import retry

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


def purge_urls(key: str) -> Optional[Tuple[Identifier, List[str]]]:
    """
    Parameters
    ----------
    key: GS key should not start with a / ex. `ftp/arxiv/papers/1901/1901.0001.abs`

    paperid: The paper ID this is related to

    Returns
    -------
    List of paths to invalidate at fastly. Ex `["arxiv.org/abs/1901.0001"]`
    """
    # Since it is not clear if this is the current file or an older one
    # invalidate both the versioned URL and the un-versioned current URL
    paperid = _paperid(key)
    if paperid is None:
        return None

    if key.startswith('/ftp/') or key.startswith("/orig/"):
        if key.endswith(".abs"):
            return paperid, [f"arxiv.org/abs/{paperid.idv}", f"arxiv.org/abs/{paperid.id}"]
        else:
            return paperid, [f"arxiv.org/e-print/{paperid.idv}", f"arxiv.org/e-print/{paperid.id}",
                    f"arxiv.org/src/{paperid.idv}", f"arxiv.org/src/{paperid.id}"]
    # pdf, html, ps are under /ps_cache
    elif "/pdf/" in key:
        return paperid, [f"arxiv.org/pdf/{paperid.idv}", f"arxiv.org/pdf/{paperid.id}"]
    elif '/html/' in key:
        # Note this does not invalidate any paths inside the html.tgz
        return paperid, [f"arxiv.org/html/{paperid.idv}", f"arxiv.org/html/{paperid.id}",
                # Note needs both with and without trailing slash
                f"arxiv.org/html/{paperid.idv}/", f"arxiv.org/html/{paperid.id}/"]
    elif '/ps/' in key:
        return paperid, [f"arxiv.org/ps/{paperid.idv}", f"arxiv.org/ps/{paperid.id}"]
    elif '/dvi/' in key:
        return paperid, [f"arxiv.org/dvi/{paperid.idv}", f"arxiv.org/dvi/{paperid.id}"]
    else:
        return paperid, []


class Invalidator:
    def __init__(self, fastly_url: str, fastly_api_token: str, always_soft_purge: bool=False, dry_run: bool=False) -> None:
        if fastly_url.endswith("/"):
            self.fastly_url = fastly_url[:-1]
        else:
            self.fastly_url = fastly_url
        self.fastly_api_token = fastly_api_token
        self.always_soft_purge = always_soft_purge
        self.dry_run = dry_run

    @retry.Retry()
    def invalidate(self, arxiv_url: str, paperid: Identifier, soft_purge: bool=False) -> None:
        headers = {"Fastly-Key": self.fastly_api_token}
        if self.always_soft_purge or soft_purge:
            headers["fastly-soft-purge"] = "1"

        url = f"{self.fastly_url}/{arxiv_url}"

        if self.dry_run:
            logging.info(f"{paperid.idv} DRY_RUN: Would have requested '{url}'")
            return

        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            print(f"{paperid.idv} purged {arxiv_url}")
            logging.info(f"{paperid.idv} purged {arxiv_url}")
            return
        if 400 <= resp.status_code < 500 and resp.status_code not in [429, 408]:
            logging.error(f"Purge failed. GET req to {url} failed: {resp.status_code} {resp.text}")
            return
        else:
            resp.raise_for_status()


def invalidate_for_gs_change(bucket: str, key: str, invalidator: Invalidator) -> None:
    tup = purge_urls(key)
    if not tup:
        logging.info(f"No purge: gs://{bucket}/{key} not related to an arxiv paper id")
        return
    paper_id, paths = tup
    if not paths:
        logging.info(f"No purge: gs://{bucket}/{key} Related to {paper_id.idv} but no paths")
        return
    for path in paths:
            try:
                invalidator.invalidate(path, paper_id)
            except Exception as exc:
                logging.error(f"Purge failed: {path} failed {exc}")


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
