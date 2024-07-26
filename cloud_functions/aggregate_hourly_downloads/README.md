# summary
aggregates hourly download stats into a table grouping by category, country and download type. In response to a pubsub takes data from arxiv_stats.papers_downloaded_by_ip_recently. Looks up the categories for each paper from our main database and aggregates the data. Then writes this to another table SOMEWHERE TBD

# commands

to install 
` pip install -r src/requirements.txt `
and 
` pip install -r src/requirements-dev.txt `

to set up enviroment variables

```
export ENVIRONMENT='PRODUCTION'
export LOG_LEVEL='INFO'
export CLASSIC_DB_URI='SECRET_HERE'
```

to run 
` functions-framework --target=aggregate_hourly_downloads --signature-type=cloudevent `

message data options:
TBD

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

to run tests 
` pytest tests `