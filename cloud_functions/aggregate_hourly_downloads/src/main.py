import json
import base64
import os

import logging
from google.cloud.logging import Client
from google.cloud.logging.handlers import CloudLoggingHandler

import functions_framework
from cloudevents.http import CloudEvent

from google.cloud import bigquery

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
        query = """
        SELECT * FROM arxiv-production.arxiv_stats.papers_downloaded_by_ip_recently LIMIT 10
        """
        
        query_job = bq_client.query(query)
        results = query_job.result() 
        for row in results:
            paper_id = row[0]
            geo_country = row[1]
            continent = row[2]
            start_dttm = row[3]
            num_downloads = row[4]
            print(f"Paper ID: {paper_id}, Country: {geo_country}, Continent: {continent}, Start Date: {start_dttm}, Downloads: {num_downloads}")
            
    else:
        logger.info(f"Unknown Enviroment: {enviro}")

