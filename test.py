import argparse
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1alpha

def sample_get_engine(project_id, location, engine_id):
    # project_id = "mikelaramie-sparkai-sandbox"
    # location = "us"          # Values: "global", "us", "eu"
    # engine_id = "example-engine-id"

    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # Create a client
    engClient = discoveryengine_v1alpha.EngineServiceClient(
        client_options=client_options
    )
    # astClient = discoveryengine_v1alpha.AssistantServiceClient(
    #     client_options=client_options
    # )

    # Initialize request argument(s)
    request = discoveryengine_v1alpha.GetEngineRequest(
        name=f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}"
    )

    # Make the request
    engResponse = engClient.get_engine(request=request)

    # Handle the response
    if engResponse.solution_type == 2:  #'SOLUTION_TYPE_SEARCH - https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.SolutionType
    #     astRequest = discoveryengine_v1alpha.Get (
    #     name=f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}"
    # )astResponse = (client.get_assistant)
        print(engResponse)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("simple_example")
    parser.add_argument("project_id", help="The project ID for the engine to check", type=str)
    parser.add_argument("location", help="The location of the engine to check (Must be 'us', 'eu', or 'global')", type=str)
    parser.add_argument("engine_id", help="The engine ID for the engine to check", type=str)
    args = parser.parse_args()
    sample_get_engine(args.project_id, args.location, args.engine_id)
