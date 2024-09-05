import json
import base64
from cloudevents.http import CloudEvent

import logging
import functions_framework
functions_framework.setup_logging()

@functions_framework.http
def hello_world_http(request):
    logging.warning("a log")
    return f"Hello world! data: {request}"

@functions_framework.cloud_event
def hello_world(cloud_event: CloudEvent):
    event_data=cloud_event.get_data()
    logging.warning(f"Event Data: {event_data}")
    logging.warning(f"Event Attributes: {cloud_event.get_attributes()}")

    logging.warning (f"msg: {event_data['message']}")
    data=base64.b64decode(event_data['message']['data']).decode()
    logging.warning(f"Decoded: {data}")
    info=json.loads(data)
    logging.warning(f"JSON data: {info.get('foo')}")
    return