from google.cloud import asset_v1
from google.cloud.discoveryengine_v1 import AssistantServiceClient
#from googleapiclient.discovery import build
from google.api_core.client_options import ClientOptions
import google.auth
import google.auth.transport.requests
import requests
import json

creds, project = google.auth.default()
auth_req = google.auth.transport.requests.Request()
creds.refresh(auth_req)
token = creds.token

org_id = "427988568354"
project_id = "mikelaramie-sparkai-sandbox"
asset_types = ["discoveryengine.googleapis.com/Engine"]
#content_type = 
page_size = 1000

project_resource = f"projects/{project_id}"
org_resource = f"organizations/{org_id}"


def get_engines(parent):
# Call ListAssets v1 to list assets
    assetClient = asset_v1.AssetServiceClient()
    assetResponse = assetClient.list_assets(
        request={
            "parent": parent,
            "read_time": None,
            "asset_types": asset_types,
            #"content_type": content_type,
            "page_size": page_size,
        }
    )
    return assetResponse

if __name__ == "__main__":
    for engine in get_engines(org_resource):

        message_data = {
            "engineId": engine,
            #TODO: Clean up faults
            "fault": {
                "code": None,
                "reason": None
            },
            "features": {
                "disable-video-generation": None,
                "disable-image-generation": None,
                "disable-talk-to-content": None,
                "bi-directional-audio": None
            },
            "maConfig": {
                "maPromptTemplate": None,
                "maResponseTemplate": None,
                "maFailureMode": None
            },
            "cmekConfig": {
                "kmsKey": None,
                "state": None,
                "notebooklmState": None
            }
        }

        # //discoveryengine.googleapis.com/projects/1234567890123/locations/us/collections/default_collection/engines/example-engine-id
        engEndpoint = engine.name.removeprefix("//discoveryengine.googleapis.com/")
        # projects/1234567890123/locations/us/collections/default_collection/engines/example-engine-id
        engSplitEndpoint = engEndpoint.split("/")
        
        engLocation = engSplitEndpoint[3] # us
        engProject = engSplitEndpoint[1] # 1234567890123
        engName = engSplitEndpoint[len(engSplitEndpoint)-1] # example-engine-id

        api_endpoint = (
            f"{engLocation}-discoveryengine.googleapis.com"
            if engLocation != "global"
                else "discoveryengine.googleapis.com"
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Goog-User-Project": engProject,
            "Content-Type": "application/json"
        }
        astApiVersion = "v1alpha"
        cmekApiVersion = "v1"
        engApiVersion = "v1alpha"
        
        engUrl = f"https://{api_endpoint}/{engApiVersion}/{engEndpoint}/"
        astUrl = f"https://{api_endpoint}/{astApiVersion}/{engEndpoint}/assistants/default_assistant"
        cmekUrl = f"https://{api_endpoint}/{cmekApiVersion}/projects/{engProject}/locations/{engLocation}/cmekConfigs/default_cmek_config"
        
        astResponse = requests.get(astUrl, headers=headers )
        if astResponse.status_code == 200:
            message_data["engineId"] = engEndpoint
            astData = astResponse.json()
            ma_policy = astData.get('customerPolicy',{})
            model_armor_config = ma_policy.get('modelArmorConfig')
            
            if model_armor_config:
                if model_armor_config.get('userPromptTemplate'):
                    message_data["maConfig"]["maPromptTemplate"] = model_armor_config.get('userPromptTemplate')
                else: 
                    message_data["fault"]["code"] = 1
                    message_data["fault"]["reason"] = "MODELARMOR: No User Prompt Template configured"
                if model_armor_config.get('responseTemplate'):
                    message_data["maConfig"]["maResponseTemplate"] = model_armor_config.get('responseTemplate')
                else: 
                    message_data["fault"]["code"] = 1
                    message_data["fault"]["reason"] = "MODELARMOR: No User Prompt Template configured"
                message_data["maConfig"]["maFailureMode"] = str(model_armor_config.get('failureMode'))
                if str(model_armor_config.get('failureMode')) != "FAIL_CLOSED":
                    message_data["fault"]["code"] = 1
                    message_data["fault"]["reason"] = "MODELARMOR: Failure Mode set incorrectly"
                else:
                    message_data["maConfig"]["maFailureMode"] = str(model_armor_config.get('failureMode'))
            
            else:
                message_data["fault"]["code"] = 1
                message_data["fault"]["reason"] = "MODELARMOR: Model Armor not configured"
            
            cmekResponse = requests.get(cmekUrl, headers=headers )
            if cmekResponse.status_code == 200:
                #TODO: Add Single Region Key checks
                #TODO: Add state/nblm checks
                cmekData = cmekResponse.json()
                if cmekData.get('kmsKey'):
                    message_data["cmekConfig"]["kmsKey"] = cmekData.get('kmsKey')
                    message_data["cmekConfig"]["state"] = cmekData.get('state')
                    message_data["cmekConfig"]["notebooklmState"] = cmekData.get('notebooklmState')
                else:
                    message_data["fault"]["code"] = 1
                    message_data["fault"]["reason"] = "CMEK: CMEK not configured"

            engResponse = requests.get(engUrl, headers=headers)
            if engResponse.status_code == 200:
                #TODO: Add more robust feature handling
                engData = engResponse.json()
                feature_config = engData.get('features')
                if feature_config:
                    message_data["features"]["bi-directional-audio"] = feature_config.get('bi-directional-audio')
                    message_data["features"]["disable-image-generation"] = feature_config.get('disable-image-generation')
                    message_data["features"]["disable-talk-to-content"] = feature_config.get('disable-talk-to-content')
                    message_data["features"]["disable-video-generation"] = feature_config.get('disable-video-generation')
                else:
                    message_data["fault"]["code"] = 1
                    message_data["fault"]["reason"] = "FEATURES: Could not get feature config"

            #if message_data["fault"]["code"]:
            print(json.dumps(message_data))

        else:
            print("Issue calling Engine config for" + engEndpoint)
        
    # astClient = AssistantServiceClient(client_options=client_options)
    # astResponse = astClient.get
    # service = build("discoveryengine","v1", credentials=creds, client_options=client_options)
    # assistant = service.projects().locations().collections().engines().assistants().get(name="projects/852844320409/locations/us/collections/default_collection/engines/example-engine-id/assistants/default_assistant")
    # assistant.execute()