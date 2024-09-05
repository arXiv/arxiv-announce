import json
import base64
from cloudevents.http import CloudEvent

# init check: which handlers, if any
import functions_framework
from functions_framework import logging

# sanity check: avoid "surprise" handlers.
# Only use the 2 provided by functions_framework (stdout, stderr)
init_logger = logging.getLogger()
if init_logger.hasHandlers:
    for handler in init_logger.handlers:
        init_logger.removeHandler(handler)

functions_framework.setup_logging()

@functions_framework.http
def hello_world_http(request):
    handlers = logging.getLogger().handlers
    logging.info (f"Handlers: {handlers}")
    logging.debug(f"Debug")
    logging.warning(f"Warning")
    logging.error(f"Error")
    logging.critical(f"Critical")
    logging.exception(f"Exception")
    return f"Hello world! data: {request}"

@functions_framework.cloud_event
def hello_world(cloud_event: CloudEvent):
    event_data=cloud_event.get_data()
    handlers = logging.getLogger().handlers
    logging.info (f"Handlers: {handlers}")
    logging.debug(f"Debug")
    logging.warning(f"Warning")
    logging.error(f"Error")
    logging.critical(f"Critical")
    logging.exception(f"Exception")
    logging.info (f"Event Data: {event_data}")
    logging.info (f"Event Attributes: {cloud_event.get_attributes()}")

    logging.info (f"msg: {event_data['message']}")
    data=base64.b64decode(event_data['message']['data']).decode()
    logging.info(f"Decoded: {data}")
    info=json.loads(data)
    logging.info(f"JSON data: {info.get('foo')}")
    return