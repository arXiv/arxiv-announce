# Summary
Listens an listen to bucket change events and will purge at fastly based on
the object changed in the bucket.

Env vars:

- FASTLY_API_TOKEN required, configure from secrets
- FASTLY_URL optional, default is correct for fastly
- ALWAYS_SOFT_PURGE optional, defaults off 1 or 0
- DRY_RUN optional, defaults to off, 1 or 0

Deploy with something like:

  SA=fastly-invalidator@arxiv-production.iam.gserviceaccount.com
  # needs access to secret fastly-purge-token

  # default compute SA
  TRIGGER_SA=1090350072932-compute@developer.gserviceaccount.com

  gcloud functions deploy purge_on_obj_change \
   --retry --gen2 \
   --source ./ \
   --runtime python311  \
   --region us-central1 \
   --trigger-bucket arxiv-production-data \
   --trigger-location us \
   --trigger-service-account=$TRIGGER_SA \
   --entry-point main \
   --service-account $SA \
   --set-secrets "FASTLY_API_TOKEN=fastly-purge-token:latest" \
   --allow-unauthenticated





# commands

to install 
` pip install -r src/requirements.txt `
and 
` pip install -r src/requirements-dev.txt `

to set up enviroment variables
TODO

```
export ENVIRONMENT='PRODUCTION'
export LOG_LEVEL='INFO'
export CLASSIC_DB_URI='SECRET_HERE'
export FASTLY_PURGE_TOKEN='SECRET_HERE'
```

to run 
` functions-framework --target=purge_on_bucket_change --signature-type=cloudevent `

message data options:
{"paper_id":"1008.3222", "old_categories":"Not specified"} : "eyJwYXBlcl9pZCI6IjEwMDguMzIyMiIsICJvbGRfY2F0ZWdvcmllcyI6Ik5vdCBzcGVjaWZpZWQifQ=="
{"paper_id":"1008.3222", "old_categories":"eess.SY hep-lat"} : "eyJwYXBlcl9pZCI6IjEwMDguMzIyMiIsICJvbGRfY2F0ZWdvcmllcyI6ImVlc3MuU1kgaGVwLWxhdCJ9"

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
        "message": {
          "data": "eyJwYXBlcl9pZCI6IjEwMDguMzIyMiIsICJvbGRfY2F0ZWdvcmllcyI6ImVlc3MuU1kgaGVwLWxhdCJ9",
          "attributes": {
             "attr1":"attr1-value"
          }
        },
        "subscription": "projects/MY-PROJECT/subscriptions/MY-SUB"
      }'
    
 ```

to run tests (these only ensure the function in base is called correctly, actual logic lives in base)
` pytest tests `