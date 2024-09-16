import json
import base64
import os

import functions_framework
from cloudevents.http import CloudEvent

from arxiv.integration.fastly.purge import purge_cache_for_paper
from arxiv.identifier import IdentifierException

#logging setup
if not(os.environ.get('LOG_LOCALLY')):
    import google.cloud.logging
    client = google.cloud.logging.Client()
    client.setup_logging()
import logging 
log_level_str = os.getenv('LOG_LEVEL', 'INFO')
log_level = getattr(logging, log_level_str.upper(), logging.INFO)
logging.basicConfig(level=log_level)

@functions_framework.cloud_event
def purge_all_for_paper(cloud_event: CloudEvent):
    """ this function purges everything to do with a particular paper, inlcuding list pages it is on.
    old_cats is used in case fo a category change to also refresh any lists the paper was removed from, and any year tallies its been added to or removed from
    """

    data=json.loads(base64.b64decode(cloud_event.get_data()['message']['data']).decode())
    logging.info(f"Received message: {data}")
    paper= data.get("paper_id")
    old_cats= data.get("old_categories")
    enviro=os.environ.get('ENVIRONMENT')
    if enviro == "PRODUCTION":
        try:
            if old_cats=="Not specified":
                purge_cache_for_paper(paper)
            else:
                purge_cache_for_paper(paper, old_cats)
        #log message structure errors and acknowledge so they don't repeat    
        except KeyError as e:
            logging.error(f"Bad category string in old_categories: {old_cats}. Info: {e}")
        except IdentifierException as e:
            logging.error(f"Invalid paper_id provided: {paper}. Info: {e}")
    else:
        logging.info(f"Purge request ignored for non-production environment. Enviroment: {enviro} paper_id: {paper} old_categories: {old_cats}")

