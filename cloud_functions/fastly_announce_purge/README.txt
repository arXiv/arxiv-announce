this function gets called by a pubsub event when announce is finsihed and send fastly various announce related purge requests
it gets triggered with a message that looks like '{"event":"announcement_complete"}'


run the function locally:
need to set CLASSIC_DB_URI and FASTLY_PURGE_TOKEN if you want to actually purge something

run this in src folder
`functions-framework --target=purge_for_announce --signature-type=cloudevent`

and trigger with

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
         "data": "eyJldmVudCI6ImFubm91bmNlbWVudF9jb21wbGV0ZSJ9",
         "attributes": {
            "attr1":"attr1-value"
         }
       },
       "subscription": "projects/MY-PROJECT/subscriptions/MY-SUB"
     }'
   
```