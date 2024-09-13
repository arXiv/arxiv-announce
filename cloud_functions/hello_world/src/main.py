import json
import base64
import os
import functions_framework
from cloudevents.http import CloudEvent

# quick and dirty override to get some logging verbosity on localhost
if not(os.environ.get('LOG_LOCALLY')):
    #cloud function logging setup
    import google.cloud.logging
    client = google.cloud.logging.Client()
    client.setup_logging()

import logging 
log_level_str = os.getenv('LOG_LEVEL', 'INFO')
log_level = getattr(logging, log_level_str.upper(), logging.INFO)
logging.basicConfig(level=log_level)

@functions_framework.http
def hello_world_http(request):
    try:
        handlers = logging.getLogger().handlers
        logging.info (f"Handlers: {handlers}")
        logging.debug(f"Debug log")
        logging.warning(f"Warning log")
        logging.error(f"Error log")
        logging.critical(f"Critical log")
    except Exception as e:
        logging.error("Exception ", e)
    return f"Hello world! data: {request}"

@functions_framework.cloud_event
def hello_world(cloud_event: CloudEvent):
    event_data=cloud_event.get_data()
    logging.info (f"Event Data: {event_data}")
    logging.info (f"Event Attributes: {cloud_event.get_attributes()}")
    logging.info (f"msg: {event_data['message']}")
    data=base64.b64decode(event_data['message']['data']).decode()
    logging.info(f"Decoded: {data}")
    info=json.loads(data)
    logging.info(f"JSON data: {info.get('foo')}")
    return