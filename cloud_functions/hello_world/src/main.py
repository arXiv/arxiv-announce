import json
import base64

import functions_framework
from cloudevents.http import CloudEvent

@functions_framework.http
def hello_world_http(request):
    print("a log")
    return f"Hello world! data: {request}"

@functions_framework.cloud_event
def hello_world(cloud_event: CloudEvent):
    event_data=cloud_event.get_data()
    print (f"Event Data: {event_data}")
    print (f"Event Attributes: {cloud_event.get_attributes()}")

    print (f"msg: {event_data['message']}")
    data=base64.b64decode(event_data['message']['data']).decode()
    print(f"Decoded: {data}")
    info=json.loads(data)
    print(f"JSON data: {info.get('foo')}")
    return