import json
import base64
import os
from typing import Set, Dict, List

from arxiv.taxonomy.category import Category
from arxiv.taxonomy.definitions import ARCHIVES_SUBSUMED, CATEGORY_ALIASES, CATEGORIES
from arxiv.db import session
from arxiv.db.models import Metadata, DocumentCategory

import logging
from google.cloud.logging import Client
from google.cloud.logging.handlers import CloudLoggingHandler

import functions_framework
from cloudevents.http import CloudEvent

from google.cloud import bigquery
from sqlalchemy.orm import aliased
from sqlalchemy import func

#cloud function logging setup
handler = CloudLoggingHandler(Client())
functions_framework.setup_logging()
logger = logging.getLogger(__name__)
log_level_str = os.getenv('LOG_LEVEL', 'INFO')
log_level = getattr(logging, log_level_str.upper(), logging.INFO)
logger.setLevel(log_level)
logger.addHandler(handler)

# Initialize BigQuery client
bq_client = bigquery.Client()

class PaperCategories:
    paper_id: str
    primary : Category
    crosses: Set[Category]

    def __init__(self, id:str):
        self.paper_id=id
        self.primary=None
        self.crosses=set()

    def add_primary(self,cat:str):
        if self.primary != None: #this function should only get called once per paper
            logger.error(f"Multiple primary categories for {self.paper_id}: {self.primary} and {cat}")
            self.add_cross(cat) #add as a cross just to keep data
        else:
            catgory=CATEGORIES[cat]
            canon=catgory.get_canonical()
            self.primary=canon
            self.crosses.discard(canon) #removes from crosses if present

    def add_cross(self, cat:str):
        catgory=CATEGORIES[cat]
        canon=catgory.get_canonical()
        #avoid dupliciates of categories with other names
        if self.primary is None or canon != self.primary:
            self.crosses.add(canon)

    def __repr__(self):
        crosses_str = ', '.join(cat.id for cat in self.crosses)
        return f"Paper: {self.paper_id} Primary: {self.primary.id} Crosses: {crosses_str}"


@functions_framework.cloud_event
def aggregate_hourly_downloads(cloud_event: CloudEvent):
    """ get downloads data and aggregate but category country and download type
    """

    data=json.loads(base64.b64decode(cloud_event.get_data()['message']['data']).decode())
    logger.info(f"Received message: {data}")
    enviro=os.environ.get('ENVIRONMENT')
    if enviro == "PRODUCTION":
        pass
    elif enviro == "DEVELOPMENT":

        #get the download data
        query = """
            SELECT 
                paper_id, 
                geo_country, 
                continent, 
                start_dttm, 
                num_downloads 
            FROM arxiv-production.arxiv_stats.papers_downloaded_by_ip_recently 
            LIMIT 5
        """
        query_job = bq_client.query(query)
        download_data = query_job.result() 

        #get all the paper_ids
        paper_ids=[]
        for row in download_data:
            paper_ids.append(row['paper_id'])

        #get the category data for papers
        meta=aliased(Metadata)
        dc=aliased(DocumentCategory)    
        paper_cats = (
            session.query(meta.paper_id, dc.category, dc.is_primary)
            .join(meta, dc.document_id == meta.document_id)
            .filter(meta.paper_id.in_(paper_ids)) 
            .filter(meta.is_current==1)
            .all()
        )
        
        #format paper categories into dictionary
        paper_categories: Dict[str, PaperCategories]={}
        for row in paper_cats:
            paper_id, cat, is_primary = row
            entry=paper_categories.setdefault(paper_id, PaperCategories(paper_id))
            if is_primary ==1:
                entry.add_primary(cat)
            else:
                entry.add_cross(cat)


        # for row in download_data:

        #     paper_id = row['paper_id']
        #     geo_country = row['geo_country']
        #     continent = row['continent']
        #     start_dttm = row['start_dttm']
        #     num_downloads = row['num_downloads']
        #     print(f"Paper ID: {paper_id}, Country: {geo_country}, Continent: {continent}, Start Date: {start_dttm}, Downloads: {num_downloads}")
            


    else:
        logger.info(f"Unknown Enviroment: {enviro}")

