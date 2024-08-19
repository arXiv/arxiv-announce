import json
import base64
import logging
import functions_framework
from cloudevents.http import CloudEvent
logging.basicConfig(level=logging.INFO)

@functions_framework.http
def hello_world_http(request):
    logging.info("a log")
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