from google.cloud import asset_v1
import google.auth
import google.auth.transport.requests
import requests
import json
import argparse

creds, project = google.auth.default()
auth_req = google.auth.transport.requests.Request()
creds.refresh(auth_req)
token = creds.token

asset_types = ["discoveryengine.googleapis.com/Engine"]
page_size = 1000

def get_engines(parent):
    """Lists all Discovery Engine assets for a given parent.

    Args:
        parent: The parent resource name, such as
            "projects/{project_id}" or "organizations/{organization_id}".

    Returns:
        An iterator of Asset objects.
    """
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


def parse_engine_name(engine_name):
    """Parses the engine name to extract relevant information."""
    engEndpoint = engine_name.removeprefix("//discoveryengine.googleapis.com/")
    engSplitEndpoint = engEndpoint.split("/")
    
    engLocation = engSplitEndpoint[3]
    engProject = engSplitEndpoint[1]
    engName = engSplitEndpoint[-1]
    
    return engEndpoint, engLocation, engProject, engName

def get_api_endpoint(engLocation):
    """Constructs the API endpoint based on the engine location."""
    return (
        f"{engLocation}-discoveryengine.googleapis.com"
        if engLocation != "global"
        else "discoveryengine.googleapis.com"
    )

def make_api_request(url, headers):
    """Makes a GET request to the specified URL and returns the JSON response."""
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def get_assistant_data(api_endpoint, engEndpoint, headers):
    """Retrieves and processes assistant data."""
    astApiVersion = "v1alpha"
    astUrl = f"https://{api_endpoint}/{astApiVersion}/{engEndpoint}/assistants/default_assistant"
    astData = make_api_request(astUrl, headers)
    
    message_data = {"faults": []}
    if astData:
        message_data["engineId"] = engEndpoint
        ma_policy = astData.get('customerPolicy', {})
        model_armor_config = ma_policy.get('modelArmorConfig')
        
        if model_armor_config:
            message_data["maConfig"] = {
                "maPromptTemplate": model_armor_config.get('userPromptTemplate'),
                "maResponseTemplate": model_armor_config.get('responseTemplate'),
                "maFailureMode": str(model_armor_config.get('failureMode'))
            }
            if not model_armor_config.get('userPromptTemplate'):
                message_data["faults"].append({"code": 101, "reason": "MODELARMOR: No User Prompt Template configured"})
            if not model_armor_config.get('responseTemplate'):
                message_data["faults"].append({"code": 102, "reason": "MODELARMOR: No Response Template configured"})
            if str(model_armor_config.get('failureMode')) != "FAIL_CLOSED":
                message_data["faults"].append({"code": 103, "reason": "MODELARMOR: Failure Mode set incorrectly"})
        else:
            message_data["faults"].append({"code": 104, "reason": "MODELARMOR: Model Armor not configured"})
    else:
        message_data["faults"].append({"code": 105, "reason": f"ASSISTANT: Could not get assistant config for {engEndpoint}"})    
    return message_data

def get_cmek_data(api_endpoint, engProject, engLocation, headers):
    """Retrieves and processes CMEK data."""
    cmekApiVersion = "v1"
    cmekUrl = f"https://{api_endpoint}/{cmekApiVersion}/projects/{engProject}/locations/{engLocation}/cmekConfigs/default_cmek_config"
    cmekData = make_api_request(cmekUrl, headers)
    
    message_data = {"faults": []}
    if cmekData and cmekData.get('kmsKey'):
        message_data["cmekConfig"] = {
            "kmsKey": cmekData.get('kmsKey'),
            "state": cmekData.get('state'),
            "notebooklmState": cmekData.get('notebooklmState')
        }
        if cmekData.get('notebooklmState') != "NOTEBOOK_LM_READY":
            message_data["faults"].append({"code": 202, "reason": "CMEK: notebooklmState is not ready"})
        if cmekData.get('state') != "ACTIVE":
            message_data["faults"].append({"code": 203, "reason": "CMEK: State is not active"})
    else:
        message_data["faults"].append({"code": 201, "reason": "CMEK: CMEK not configured"})
        
    return message_data

def get_engine_data(api_endpoint, engEndpoint, headers):
    """Retrieves and processes engine feature data."""
    engApiVersion = "v1alpha"
    engUrl = f"https://{api_endpoint}/{engApiVersion}/{engEndpoint}/"
    engData = make_api_request(engUrl, headers)
    
    message_data = {"faults": []}
    if engData and engData.get('features'):
        feature_config = engData.get('features')
        message_data["features"] = {
            "bi-directional-audio": feature_config.get('bi-directional-audio'),
            "disable-image-generation": feature_config.get('disable-image-generation'),
            "disable-talk-to-content": feature_config.get('disable-talk-to-content'),
            "disable-video-generation": feature_config.get('disable-video-generation')
        }
        if feature_config.get('disable-video-generation') != "FEATURE_STATE_ON":
            message_data["faults"].append({"code": 302, "reason": "FEATURES: disable-video-generation is not ON"})
        if feature_config.get('disable-image-generation') != "FEATURE_STATE_ON":
            message_data["faults"].append({"code": 303, "reason": "FEATURES: disable-image-generation is not ON"})
        if feature_config.get('disable-talk-to-content') != "FEATURE_STATE_ON":
            message_data["faults"].append({"code": 304, "reason": "FEATURES: disable-talk-to-content is not ON"})
        if feature_config.get('bi-directional-audio') != "FEATURE_STATE_OFF":
            message_data["faults"].append({"code": 305, "reason": "FEATURES: bi-directional-audio is not OFF"})
    else:
        message_data["faults"].append({"code": 301, "reason": "FEATURES: Could not get feature config"})
        
    return message_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check Discovery Engine configurations for a given organization."
    )
    parser.add_argument("--org_id", required=True, help="The organization ID.")
    parser.add_argument("--project_id", required=True, help="The project ID.")
    args = parser.parse_args()

    org_resource = f"organizations/{args.org_id}"

    for engine in get_engines(org_resource):
        engEndpoint, engLocation, engProject, engName = parse_engine_name(engine.name)
        
        api_endpoint = get_api_endpoint(engLocation)
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Goog-User-Project": engProject,
            "Content-Type": "application/json"
        }
        
        message_data = {
            "engineId": engEndpoint,
            "faults": [],
            "features": {},
            "maConfig": {},
            "cmekConfig": {}
        }
        
        assistant_data = get_assistant_data(api_endpoint, engEndpoint, headers)
        if assistant_data:
            message_data["faults"].extend(assistant_data.get("faults", []))
            assistant_data.pop("faults", None)
            message_data.update(assistant_data)

        cmek_data = get_cmek_data(api_endpoint, engProject, engLocation, headers)
        if cmek_data:
            message_data["faults"].extend(cmek_data.get("faults", []))
            cmek_data.pop("faults", None)
            message_data.update(cmek_data)

        engine_data = get_engine_data(api_endpoint, engEndpoint, headers)
        if engine_data:
            message_data["faults"].extend(engine_data.get("faults", []))
            engine_data.pop("faults", None)
            message_data.update(engine_data)
            
        print(json.dumps(message_data))