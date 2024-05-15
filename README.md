# arxiv-announce
Collection of functions used for the announce process


# organization 
For each function make a subfolder under cloud_functions. 
In that folder include the source files, requirements.txt, tests, and cicd files it may need. 

The hello_world folder has a simple cloud_function you can make a copy of to get started

# running locally

for http driven functions:

to run your cloud function, run this in the src directory and name your target function
` functions-framework --target=hello_world_http`

to trigger you can go to http://127.0.0.1:8080/ in your browser

for cloud event driven functions:

to run your cloud function
` functions-framework --target=hello_world --signature-type=cloudevent `

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
          "data": "eyJmb28iOiJiYXIifQ==",
          "attributes": {
             "attr1":"attr1-value"
          }
        },
        "subscription": "projects/MY-PROJECT/subscriptions/MY-SUB"
      }'
    
 ```