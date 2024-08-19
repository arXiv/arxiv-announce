import json
import base64
import logging
from cloudevents.http import CloudEvent

import traceback
import types

def addh_st(self, hdlr):
     print(f"About to add {hdlr} at")
     print("___________ stacktrace ____________")
     traceback.print_stack()
     print("__________ end stacktrace _________")
     self.__class__.addHandler(self, hdlr)

     
root_h = logging.getLogger()
root_h.addHandler = types.MethodType(addh_st, root_h)
root_h.addHandler(logging.StreamHandler())


import functions_framework
functions_framework.setup_logging()

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