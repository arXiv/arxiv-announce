import json
import base64
import os

import logging
from google.cloud.logging import Client
from google.cloud.logging.handlers import CloudLoggingHandler

import functions_framework
from cloudevents.http import CloudEvent

from arxiv.integration.fastly.purge import purge_cache_for_paper

#cloud function logging setup
handler = CloudLoggingHandler(Client())
functions_framework.setup_logging()
logger = logging.getLogger(__name__)
log_level_str = os.getenv('LOG_LEVEL', 'INFO')
log_level = getattr(logging, log_level_str.upper(), logging.INFO)
logger.setLevel(log_level)
logger.addHandler(handler)


@functions_framework.cloud_event
def purge_all_for_paper(cloud_event: CloudEvent):
    """ this function purges everything to do with a particular paper, inlcuding list pages it is on.
    old_cats is used in case fo a category change to also refresh any lists the paper was removed from, and any year tallies its been added to or removed from
    """

    data=json.loads(base64.b64decode(cloud_event.get_data()['message']['data']).decode())
    paper= data.get("paper_id")
    old_cats= data.get("old_categories")
    if os.environ.get('ENVIRONMENT') == "PRODUCTION":
        if old_cats=="Not specified":
            purge_cache_for_paper(paper)
        else:
            purge_cache_for_paper(paper, old_cats)



