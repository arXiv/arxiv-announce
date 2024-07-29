import json
import base64
import os
from typing import Set, Dict, List, Literal
from datetime import datetime

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

DownloadType = Literal["pdf", "html", "src"]

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

class DownloadData:
    def __init__(self, paper_id: str, country: str, download_type: DownloadType, time: datetime, num: int):
        self.paper_id = paper_id
        self.country = country
        self.download_type = download_type
        self.time = time
        self.num = num

    def __repr__(self) -> str:
        return (f"DownloadData(paper_id='{self.paper_id}', country='{self.country}', "
                f"download_type='{self.download_type}', time='{self.time}', "
                f"num={self.num})")

class DownloadCounts:
    def __init__(self):
        self.primary=0
        self.cross=0

    def __repr__(self):
        return f"Count(primary: {self.primary}, cross: {self.cross})"

class DownloadKey:
    def __init__(self, time: datetime, country: str, download_type: DownloadType, category_id: str):
        self.time = time  
        self.country = country
        self.download_type = download_type
        self.category=category_id

    def __eq__(self, other):
        if isinstance(other, DownloadKey):
            return (self.time == other.time and 
                    self.country == other.country and 
                    self.download_type == other.download_type and
                    self.category == other.category
                    )
        return False

    def __hash__(self):
        return hash((self.time, self.country, self.download_type, self.category))

    def __repr__(self):
        return f"Key(type: {self.download_type}, cat: {self.category}, country: {self.country}, day: {self.time.day} hour: {self.time.hour})"

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
                download_type, 
                start_dttm, 
                num_downloads 
            FROM arxiv-production.arxiv_stats.papers_downloaded_by_ip_recently 
            LIMIT 5
        """
        query_job = bq_client.query(query)
        download_result = query_job.result() 

        #process and store returned data
        paper_ids=set() #only look things up for each paper once
        download_data: List[DownloadData]=[] #not a dictionary because no unique keys
        for row in download_result:
            download_data.append(
                DownloadData(
                    paper_id=row['paper_id'],
                    country=row['geo_country'],
                    download_type=row['download_type'],
                    time=row['start_dttm'].replace(minute=0, second=0, microsecond=0), #bucketing by hour
                    num=row['num_downloads']
                )
            )
            paper_ids.add(row['paper_id'])
        
        #find categories for all the papers
        paper_categories=get_paper_categories(paper_ids)

        #aggregate download data
        all_data: Dict[DownloadKey, DownloadCounts]={}
        for entry in download_data:
            cats=paper_categories[entry.paper_id]
            #record primary
            key=DownloadKey(entry.time, entry.country, entry.download_type, cats.primary.id)
            value=all_data.get(key, DownloadCounts())
            value.primary+=entry.num
            all_data[key]=value
            
            #record for each cross
            for cat in cats.crosses:
                key=DownloadKey(entry.time, entry.country, entry.download_type, cat.id)
                value=all_data.get(key, DownloadCounts())
                value.cross+=entry.num
                all_data[key]=value


    else:
        logger.info(f"Unknown Enviroment: {enviro}")




def get_paper_categories(paper_ids: List[str])-> Dict[str, PaperCategories]:
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

    return paper_categories

