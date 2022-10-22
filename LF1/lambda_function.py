"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages reservations.
This Lambda was adapted from the 'OrderFlowers' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""
import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')
        
def send_sqs_message(url, message):
    client = boto3.client("sqs")
    response = client.send_message(QueueUrl= url, MessageBody = json.dumps(message))


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

def validate_create_reservation(location, date, time, cuisine, party_size, email_address):
    cuisine_type = ['italian', 'american', 'indpak', 'japanese', 'chinese']
    if cuisine is not None and cuisine.lower() not in cuisine_type:
        return build_validation_result(False,
                                       'Cuisine',
                                       'We could not find restaurants for {} food, would you like a different type of cuisine?  '
                                       'Our most popular cuisine is American'.format(cuisine))

    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'DiningDate', 'I did not understand that, what date would you like to make a reservation?')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() <= datetime.date.today():
            return build_validation_result(False, 'DiningDate', 'You can make a reservation from tomorrow onwards.  What day would you like to make a reservation?')

    if time is not None:
        if len(time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

        hour, minute = time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

        if hour < 10 or hour > 22:
            # Outside of business hours
            return build_validation_result(False, 'DiningTime', 'Standard dining hours are from ten am. to ten pm. Can you specify a time during this range?')

    if party_size is not None:
        if int(party_size) < 1 or int(party_size) > 10:
            return build_validation_result(False, 'PartySize', 'Your party size must be between one and ten people. Can you specify a party size in this range?')    

    if email_address is not None:
        if '@' not in email_address:
            return build_validation_result(False, 'EmailAddress', 'Please enter a valid email address.')    
    
    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """


def create_reservation(intent_request):
    """
    Performs dialog management and fulfillment for creating reservation.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """
    location = get_slots(intent_request)["Location"]
    date = get_slots(intent_request)["DiningDate"]
    time = get_slots(intent_request)["DiningTime"]
    cuisine = get_slots(intent_request)["Cuisine"]
    party_size = get_slots(intent_request)["PartySize"]
    email_address = get_slots(intent_request)["EmailAddress"]
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_create_reservation(location, date, time, cuisine, party_size, email_address)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        
        # Pass the price of the flowers back through session attributes to be used in various prompts defined
        # on the bot model.

        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        '''
        if flower_type is not None:
            output_session_attributes['Price'] = len(flower_type) * 5  # Elegant pricing model
        '''
        return delegate(output_session_attributes, get_slots(intent_request))

    if source == 'FulfillmentCodeHook':
        # Create the reservation, and rely on the goodbye message of the bot to define the message to the end user.
        # In a real bot, this would likely involve a call to a backend service.
        #print("Hello World")
        url = "https://sqs.us-east-1.amazonaws.com/468162644213/ChatbotQ"
        
        # Initially tried passing as a dictionary but SQS always converts to string
        #message = {"Location": location, "DiningDate": date, "DiningTime": time, "Cuisine": cuisine, "PartySize": party_size, "EmailAddress": email_address}
        # Instead pass a string delimited by whitespace and parse in LF2
        message = " {} {} {} {} {} {} ".format(location, date, time, cuisine, party_size, email_address)
        send_sqs_message(url, message)
        #print("Message Sent")
        
    return close(intent_request['sessionAttributes'],
                'Fulfilled',
                {'contentType': 'PlainText',
                'content': 'Thanks, your reservation for {} in {} at {} on {} has been made.'.format(party_size, location, time, date)})


""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionIntent':
        return create_reservation(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
