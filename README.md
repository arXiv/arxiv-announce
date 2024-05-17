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

 # deploying
  in GCP your function will need a trigger to trigger the build of the function on deploy, a service account to run the build, a service account to run the function, and well as a pubsub subscriber (or some other event) to drive it. Each function needs its own subscriber

  the dev project has a version of each of these for hello_world that can be used as a model. 
  build trigger: deploy-hello-world-cfunction
  build service account: cloudbuild-sa@arxiv-development.iam.gserviceaccount.com which you can use for all cloud builds
  function run account:announce-sa@arxiv-development.iam.gserviceaccount.com which can also be used for other function in this repositroy, or you can make your own if you want something special
  pubsub subscriber: eventarc-us-central1-hello-world-932641-sub-590 (created automatically by the cloud build)

  you can test this whole setup by publishing a message like {"foo": "magic"} in the testing topic