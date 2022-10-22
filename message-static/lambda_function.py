import json
import boto3

def lambda_handler(event, context):
    client = boto3.client('lex-runtime')
    text = event['messages'][0]['unstructured']['text']

    '''CHECKING PARSABLE EVENT OBJECT
    print("event:", event)
    print("event type", type(event))
    print("Unstructured:", event['messages'][0]['unstructured'])
    print("Unstructured Type:", event['messages'][0]['unstructured'])
    print("text:", event['messages'][0]['unstructured']['text'])
    '''

    lex_response = client.post_text(
        botName='DiningConcierge',
        botAlias='DiningConcierge',
        #userId = 'userId',
        userId='4681-6264-4213',
        inputText=text,
        activeContexts=[
        {
            'name': 'DiningRequest',
            'timeToLive': {
                'timeToLiveInSeconds': 123,
                'turnsToLive': 19
            },
            'parameters': {
                
            }
        },
        ]
    )

    lex_message = lex_response['message']
    print("Lex Response:", lex_message)

    '''' Format for message to Lex
    response = client.post_text(
    botName='string',
    botAlias='string',
    userId='string',
    sessionAttributes={
        'string': 'string'
    },
    requestAttributes={
        'string': 'string'
    },
    inputText='string',
    activeContexts=[
        {
            'name': 'string',
            'timeToLive': {
                'timeToLiveInSeconds': 123,
                'turnsToLive': 123
            },
            'parameters': {
                'string': 'string'
            }
        },
    ]
)
    '''

    message_string = {
        "messages": [
                {
                    "type": "unstructured",
                    "unstructured": {
                        "id": "string",
                        "text": lex_message,
                        "timestamp": "string"
                    }
                }
            ]
    }
    print("message_string:", message_string)
    # print("json.dumps(message_string):",type(json.dumps(message_string)))
    response =  {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST'
        },
        'body': json.dumps(message_string)
    }

    print("response:", json.dumps(response))

    return json.dumps(response)