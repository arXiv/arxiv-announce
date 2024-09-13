# Summary
Listens an listen to bucket change events and will purge at fastly based on
the object changed in the bucket.

Env vars:

- ALWAYS_SOFT_PURGE optional, defaults off 1 or 0
- DRY_RUN optional, defaults to off, 1 or 0
- FASTLY_PURGE_TOKEN, secret purge token for connecting to fastly

# commands

to install 
` pip install -r src/requirements.txt `
and 
` pip install -r src/requirements-dev.txt `


to run 
` functions-framework --target=main --signature-type=cloudevent `

message data options:
{"bucket":"arxiv-production-data", "name":"ps_cache/arxiv/html/0712/0712.3116v1/index.html"} 
{"bucket":"arxiv-production-data", "name":"ps_cache/cs/pdf/0005/0005003v1.pdf"} 

to trigger run a curl command with a cloud event, heres an example you can use: 
note that the data is base 64 encoded, and that return values from cloud functions seem to be useless
 ```
 curl localhost:8080 \
  -X POST \
  -H "Content-Type: application/json" \
  -H "ce-id: 123451234512345" \
  -H "ce-specversion: 1.0" \
  -H "ce-time: 2020-01-02T12:34:56.789Z" \
  -H "ce-type: google.cloud.pubsub.topic.v1.messagePublished" \
  -H "ce-source: //pubsub.googleapis.com/projects/MY-PROJECT/topics/MY-TOPIC" \
  -d '{
    "bucket":"arxiv-production-data", "name":"ps_cache/arxiv/html/0712/0712.3116v1/index.html"
    }'
    
 ```

to run tests if any get added
` pytest tests `