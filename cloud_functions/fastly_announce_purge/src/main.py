import json
import base64
import logging
import os

import functions_framework
from cloudevents.http import CloudEvent

from arxiv.integration.fastly.purge import purge_fastly_keys

logger = logging.getLogger(__name__)

@functions_framework.cloud_event
def purge_for_announce(cloud_event: CloudEvent):
    """ this function runs at the end of announce, purges all things from fastly that needs to be purged for the new announcement.
    functions-framework --target=purge_for_announce --signature-type=cloudevent
    """

    data=json.loads(base64.b64decode(cloud_event.get_data()['message']['data']).decode())
    event= data.get("event")
    if event =="announcement_complete":
        enviroment = os.environ.get('ENVIROMENT')
        if enviroment == "PRODUCTION":
            purge_fastly_keys("announce")
            purge_fastly_keys("announce","rss.arxiv.org")
            purge_fastly_keys("announce","export.arxiv.org")
            logger.info("Purged announcement key for production")
        elif enviroment == "DEVELOPMENT":
            purge_fastly_keys("announce", "browse.dev.arxiv.org")
            logger.info("Purged announcement key for devlopment")
        else:
            logger.warning(f"Announcement event caught, but no enviroment to purge cache. ENVIROMENT: {enviroment}")

