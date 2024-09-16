# Summary
Purges everything to do with a specific paper id, inlcuding lists it is present on.
Intended for use by the admin team for mid-day changes.
In case of a category change, providing a string of old categories allows the cache to be purged for any pages the paper has been removed from 

# commands

to install 
` pip install -r src/requirements.txt `
and 
` pip install -r src/requirements-dev.txt `

to set up enviroment variables

```
export LOG_LOCALLY=True
export ENVIRONMENT='PRODUCTION'
export LOG_LEVEL='INFO'
export CLASSIC_DB_URI='SECRET_HERE'
export FASTLY_PURGE_TOKEN='SECRET_HERE'
```

to run 
` functions-framework --target=purge_all_for_paper --signature-type=cloudevent `

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