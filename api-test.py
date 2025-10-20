from google.cloud import asset_v1
from google.cloud.discoveryengine_v1 import AssistantServiceClient
#from googleapiclient.discovery import build
from google.api_core.client_options import ClientOptions
import google.auth
import google.auth.transport.requests
import requests

creds, project = google.auth.default()
auth_req = google.auth.transport.requests.Request()
creds.refresh(auth_req)
token = creds.token

# TODO project_id = 'Your Google Cloud Project ID'
# TODO asset_types = 'Your asset type list, e.g.,
# ["storage.googleapis.com/Bucket","bigquery.googleapis.com/Table"]'
# TODO page_size = 'Num of assets in one page, which must be between 1 and
# 1000 (both inclusively)'
# TODO content_type ="Content type to list"

org_id = "427988568354"
project_id = "mikelaramie-sparkai-sandbox"
asset_types = ["discoveryengine.googleapis.com/Engine"]
#content_type = 
page_size = 1000

project_resource = f"projects/{project_id}"
org_resource = f"organizations/{org_id}"
client = asset_v1.AssetServiceClient()

# Call ListAssets v1 to list assets.
response = client.list_assets(
    request={
        "parent": org_resource, #project_resource,
        "read_time": None,
        "asset_types": asset_types,
        #"content_type": content_type,
        "page_size": page_size,
    }
)
print(token)
for asset in response:
    # //discoveryengine.googleapis.com/projects/1234567890123/locations/us/collections/default_collection/engines/example-engine-id
    engEndpoint = asset.name.removeprefix("//discoveryengine.googleapis.com/")
    # projects/1234567890123/locations/us/collections/default_collection/engines/example-engine-id
    engSplitEndpoint = engEndpoint.split("/")
    
    engLocation = engSplitEndpoint[3] # us
    engProject = engSplitEndpoint[1] # 1234567890123
    engName = engSplitEndpoint[len(engSplitEndpoint)-1] # example-engine-id

    #print(engLocation + " " + engProject + " " + engName)
    
    api_endpoint = (
        f"{engLocation}-discoveryengine.googleapis.com"
        if engLocation != "global"
            else "discoveryengine.googleapis.com"
    )
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    astApiVersion = "v1alpha"
    astUrl = f"https://{api_endpoint}/{astApiVersion}/{engEndpoint}/assistants/default_assistant"
    print(astUrl)
    astResponse = requests.get(astUrl, headers=headers )
    if astResponse.status_code == 200:
        astData = astResponse.json()
        ma_policy = astData.get('customerPolicy',{})
        model_armor_config = ma_policy.get('modelArmorConfig')
        
        if model_armor_config:
            print("Prompt Template:  " + model_armor_config.get('userPromptTemplate'))
            print("Response Template:  " + model_armor_config.get('responseTemplate'))
            print("Failure Mode:  " + str(model_armor_config.get('failureMode')))
        else:
            print('Model Armor not configured!')

    # astClient = AssistantServiceClient(client_options=client_options)
    # astResponse = astClient.get
    # service = build("discoveryengine","v1", credentials=creds, client_options=client_options)
    # assistant = service.projects().locations().collections().engines().assistants().get(name="projects/852844320409/locations/us/collections/default_collection/engines/example-engine-id/assistants/default_assistant")
    # assistant.execute()