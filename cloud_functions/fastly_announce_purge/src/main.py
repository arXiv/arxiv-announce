import json
import base64
import os
from typing import List, Tuple, Set

import functions_framework
from cloudevents.http import CloudEvent

from sqlalchemy.orm import aliased
from sqlalchemy import func

from arxiv.db import Session
from arxiv.db.models import Metadata, NextMail
from arxiv.identifier import Identifier
from arxiv.integration.fastly.purge import purge_fastly_keys
from arxiv.taxonomy.category import get_all_cats_from_string, Archive, Category, Group

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
def purge_for_announce(cloud_event: CloudEvent):
    """ this function runs at the end of announce, purges all things from fastly that needs to be purged for the new announcement.
    functions-framework --target=purge_for_announce --signature-type=cloudevent
    """

    data=json.loads(base64.b64decode(cloud_event.get_data()['message']['data']).decode())
    event= data.get("event")

    if event =="announcement_complete":
        _purge_announced_papers()

        #purge everything with daily data
        environment = os.environ.get('ENVIRONMENT')
        if environment == "PRODUCTION":
            purge_fastly_keys("announce")
            purge_fastly_keys("announce","rss.arxiv.org")
            #purge_fastly_keys("announce","export.arxiv.org") #not currently live from fastly
            logging.info("Purged announcement key for production")
        elif environment == "DEVELOPMENT":
            purge_fastly_keys("announce", "browse.dev.arxiv.org")
            logging.info("Purged announcement key for development")
        else:
            logging.warning(f"Announcement event caught, but no environment to purge cache. ENVIRONMENT: {environment}")


def _purge_announced_papers():
    """this function purges fastly's data for papers that have been created or updated since the last announcement"""
    announcements= _get_days_announcements()
    keys=_process_announcements(announcements)

    #send purge request(s) to appropriate fastly services
    environment = os.environ.get('ENVIRONMENT')
    if environment == "PRODUCTION":
        purge_fastly_keys(keys)
        #purge_fastly_keys(keys,"export.arxiv.org") #currently not in use
    elif environment == "DEVELOPMENT":
        purge_fastly_keys(keys, "browse.dev.arxiv.org")
    elif environment == "TESTING":
        logging.info(f"In TESTING enviroment. Would have purged keys {len(keys)}: {keys}\nAbove keys ({len(keys)}) not purged, in TESTING enviroment.")
    return

def _get_days_announcements()-> List[Tuple[str, int, str, str, str]]:
    """gets data for most recent days announcement
    return values are (paper_id, version, type of announcement, the papers category string, extra data (contains newly crosslisted categories))
    """
    mail= aliased(NextMail)
    meta=aliased(Metadata)
    today=Session.query(func.max(mail.mail_id)).scalar_subquery()
    result = (
        Session.query(mail.paper_id, mail.version, mail.type, meta.abs_categories, mail.extra)
        .join(meta, mail.document_id == meta.document_id)
        .filter(mail.mail_id == today)
        .filter(meta.is_current==1)
        .all()
    )
    return result

def _process_announcements(announcements:List[Tuple[str, int, str, str, str]])->List[str]:
    """ Processes the data for the mailing table to find the keys needed for each entry
    returns list of keys to purge
    parameters values are (paper_id, version, type of announcement, the papers category string, extra data (contains newly crosslisted categories))
    returns a list of all keys to purge
    """
    keys=[]
    lists=set() #also includes year pages, kept as set because of potential duplicates
    for row in announcements:
        paper_id, version, method, categories, extra= row
        keys.append(f"abs-{paper_id}") #always the abstract page

        if method == "new":
            keys.append(f"paper-id-{paper_id}-current") #all current (versionless) pages
            keys.append(f"paper-id-{paper_id}v1") #all urls with v1 in them
            #all new/recent/current lists are cleared every announce

        elif method == "cross":
            #category data appears on lists
            groups, archs, cats= get_all_cats_from_string(categories)
            arxiv_id= Identifier(paper_id)
            lists= lists | _all_list_keys(arxiv_id.year, arxiv_id.month, groups, archs, cats)

            #clear year pages that have a new number added to their count
            _, new_archs, _ = get_all_cats_from_string(extra)
            for arch in new_archs:
                lists.add(f"year-{arch.id}-{arxiv_id.year}")
        
        elif method == "rep":
            keys.append(f"paper-id-{paper_id}-current") #all current (versionless) pages
            keys.append(f"paper-id-{paper_id}v{version}") #all urls for the new version

            groups, archs, cats= get_all_cats_from_string(categories)
            arxiv_id= Identifier(paper_id)
            lists= lists | _all_list_keys(arxiv_id.year, arxiv_id.month, groups, archs, cats) #clear lists the paper is on

        elif method == "jref":
            #jrefs appear on lists
            groups, archs, cats= get_all_cats_from_string(categories)
            arxiv_id= Identifier(paper_id)
            lists= lists | _all_list_keys(arxiv_id.year, arxiv_id.month, groups, archs, cats)

        elif method == "wdr":
            keys.append(f"paper-id-{paper_id}v{version}") #all urls for the withdrawn version
            #withdrawl comments appear on lists
            groups, archs, cats= get_all_cats_from_string(categories)
            arxiv_id= Identifier(paper_id)
            lists= lists | _all_list_keys(arxiv_id.year, arxiv_id.month, groups, archs, cats)
        
    return keys + list(lists)

def _all_list_keys(year: int, month: int, groups: List[Group], archs: List[Archive], cats: List[Category])->Set[str]:
    """generates a set of all list pages a paper would be on given its year, month and categories"""
    lists=set()
    for cat in cats:
        lists.add(f"list-{year:04d}-{cat.id}") #the year listing for the category
        lists.add(f"list-{year:04d}-{month:02d}-{cat.id}") #the year and month the paper came out
    for arch in archs:
        lists.add(f"list-{year:04d}-{arch.id}") #paper also present on archive pages
        lists.add(f"list-{year:04d}-{month:02d}-{arch.id}") 
    for group in groups: #catchup filters by and tags for the physics group
        if group.id=='grp_physics':
            lists.add(f"list-{year:04d}-{month:02d}-{group.id}") 
    return lists