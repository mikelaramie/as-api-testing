
import functions_framework
from google.cloud import aiplatform

@functions_framework.http
def agentspace_settings_checker(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'agentspace_id' in request_json:
        agentspace_id = request_json['agentspace_id']
    elif request_args and 'agentspace_id' in request_args:
        agentspace_id = request_args['agentspace_id']
    else:
        return 'No agentspace_id provided.', 400

    try:
        # Initialize the AI Platform client
        aiplatform.init(project='mikelaramie-sparkai-sandbox', location='US')

        # Get the Agentspace instance
        agentspace = aiplatform.Agent.get(agentspace_id)

        # Check the model_armor_enabled setting
        model_armor_enabled = agentspace.model_armor_enabled

        return {
            'agentspace_id': agentspace_id,
            'model_armor_enabled': model_armor_enabled
        }
    except Exception as e:
        return str(e), 500
