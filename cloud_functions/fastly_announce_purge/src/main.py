import json
import base64
import os
from datetime import datetime, timezone

import logging
from google.cloud.logging import Client
from google.cloud.logging.handlers import CloudLoggingHandler

import functions_framework
from cloudevents.http import CloudEvent

from sqlalchemy.orm import aliased
from sqlalchemy import distinct,desc

from arxiv.db import session
from arxiv.db.models import Metadata, Updates
from arxiv.integration.fastly.purge import purge_fastly_keys

#cloud function logging setup
handler = CloudLoggingHandler(Client())
functions_framework.setup_logging()
logger = logging.getLogger(__name__)
log_level_str = os.getenv('LOG_LEVEL', 'INFO')
log_level = getattr(logging, log_level_str.upper(), logging.INFO)
logger.setLevel(log_level)
logger.addHandler(handler)

@functions_framework.cloud_event
def purge_for_announce(cloud_event: CloudEvent):
    """ this function runs at the end of announce, purges all things from fastly that needs to be purged for the new announcement.
    functions-framework --target=purge_for_announce --signature-type=cloudevent
    """

    data=json.loads(base64.b64decode(cloud_event.get_data()['message']['data']).decode())
    event= data.get("event")
    if event =="announcement_complete":
        purge_announced_papers()
        environment = os.environ.get('ENVIRONMENT')
        if environment == "PRODUCTION":
            purge_fastly_keys("announce")
            purge_fastly_keys("announce","rss.arxiv.org")
            purge_fastly_keys("announce","export.arxiv.org")
            logger.info("Purged announcement key for production")
        elif environment == "DEVELOPMENT":
            purge_fastly_keys("announce", "browse.dev.arxiv.org")
            logger.info("Purged announcement key for development")
        else:
            logger.warning(f"Announcement event caught, but no environment to purge cache. ENVIRONMENT: {environment}")



def purge_announced_papers():
    """this function purges fastly's data for papers that have been created or updated since the last annoucnement"""
    meta=aliased(Metadata)
    up=aliased(Updates)

    #how far into the past should be check for changes to papers
    dates = (
        session.query(distinct(up.date))
        .order_by(desc(up.date))
        .limit(2)
        .all()
    )
    days_since_last_announce=dates[0][0]-dates[1][0]
    earliest_update=datetime.now(timezone.utc) - days_since_last_announce

    #find papers that have changed since last announce
    ids=(
        session.query(meta.paper_id)
        .filter(meta.updated >=earliest_update)
        .all()
    )
    keys=[]
    for row in ids:
        keys.append(f"paper-id-{row[0]}")

    #send purge request(s) to appropriate fastly services
    environment = os.environ.get('ENVIRONMENT')
    if environment == "PRODUCTION":
        purge_fastly_keys(keys)
        purge_fastly_keys(keys,"export.arxiv.org")
    elif environment == "DEVELOPMENT":
        purge_fastly_keys(keys, "browse.dev.arxiv.org")
    return