import json
import boto3
import random
import requests

endpoint = 'https://search-restaurants-4zjgqhcwbcndtzuuiuzkm7aqoa.us-east-1.es.amazonaws.com/'
headers = { "Content-Type": "application/json" }

# getData() will return the elasticSearch result
def getData(cuisine_type):
    
    endpoint = 'https://search-restaurants-4zjgqhcwbcndtzuuiuzkm7aqoa.us-east-1.es.amazonaws.com/'
    query = '{}{}/_search?q={cuisine}&size={size_limit}'.format(endpoint, 'restaurants', cuisine=cuisine_type,size_limit=5)
    data = {}
    
    response = requests.get(query, auth=("cloud1", "nigel@CLOUD1"))
    restaurants_rawdata = json.loads(response.content.decode('utf-8'))
    restaurants_data = restaurants_rawdata['hits']['hits']
   
    # extracting restaurant_ids from Elastic Search Service
    ids = []
    for each in restaurants_data:
        ids.append(each['_source']['restaurant_id'])
      
    return random.choice(ids)


def dynamodb_query_details(business_id):
    print("business_id:", business_id)
    dynamodb_resource = boto3.resource('dynamodb')

    table = dynamodb_resource.Table("yelp-restaurants")
    
    items = table.get_item(Key={"businessId": business_id})
    
    print("items:", items)
    
    items = items["Item"]
    
    # extracting restaurant details
    restaurant_details={
     'name_of_the_restaurant' : items["name"],
     'address_of_the_restaurant' : items["address"],
     'category_of_the_restaurant' : items["category"],
     'city_of_the_restaurant' : items["city"],
     'Latitude_of_the_restaurant' : items["Latitude"],
     'Longitude_of_the_restaurant' : items["Longitude"],
     'phone_of_the_restaurant' : items["phone"],
     'rating_of_the_restaurant' : items["rating"],
     'reviewCount_of_the_restaurant' : items["reviewCount"],
     'url_of_the_restaurant' : items["url"],
     'zipcode_of_the_restaurant' : items["zipcode"]
    }
    
    return restaurant_details
    

def lambda_handler(event, context):
    client = boto3.client("ses")
    sqs_client = boto3.client("sqs")
    
    sqs_response = sqs_client.receive_message(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/468162644213/ChatbotQ',
    MaxNumberOfMessages=1,
    )

    print("SQS_response:", sqs_response)
    print("SQS_response type:", type(sqs_response))
    
    if 'Messages' not in sqs_response.keys():
        return {
            'statusCode': 200,
            'body': json.dumps("No messages in SQS!")
        }

    response = sqs_client.delete_message(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/468162644213/ChatbotQ',
    ReceiptHandle=sqs_response['Messages'][0]['ReceiptHandle']
    )

    # print("SQS_response:", sqs_response)
    # print("SQS_response type:", type(sqs_response))
    '''
    for sqs_message in sqs_response:
        print(sqs_message)
        input_string = sqs_message['Records'][0]['body']
    '''

    input_string = sqs_response['Messages'][0]['Body']

    print("Input_string:", input_string)

    #input_string = event['Records'][0]['body']
    inputs = input_string.split()
    location = inputs[1]
    date = inputs[2]
    time = inputs[3]
    cuisine = inputs[4]
    party_size = inputs[5]
    email_address = inputs[6]

    # ''' Tried mapping string to dictionary with python eval() but didn't work :(
    # input_dict = eval(input_string)
    # print("Input_dict:", input_dict)
    # print("Cuisine:", input_dict['cuisine'])
    # '''
    #print("cuisine:", cuisine)
    #cuisine_type="Chinese"
    business_id=getData(cuisine)
    restaurant_details=dynamodb_query_details(business_id)

    print(restaurant_details)

    # # query elastic search
    # UserData = getData()
    # # The below condition is used to check whether data found or not
    # if(len(UserData['hits']['hits'])==0):
    #     print("No userData Found")
    # else:
    #     for hit in UserData['hits']['hits']: #loop the data
    #         print("User Data\n",hit)
    #         # use hit['_source']['<required_filedname>'] to retreive the required feild data from your lambda
    #         print("User Name-->",hit['_source']['name'])


    subject = 'Your Reservation Suggestion'
    body = """
        <br>
        Restaurant suggestion details:
        <br>
        Name: {}
        <br>
        Address: {}, {}
        <br>
        City: {}
        <br>
        Phone Number: {}
        <br>
        Rating: {}
        <br>
        Website: {}
        <br>
        <br>
        Please see the information you provided for you restaurant suggestions. 
        <br>
        Location: {}
        <br>
        Date: {}
        <br>
        Time: {}
        <br>
        Cuisine: {}
        <br>
        Party size: {}
        <br>
        Email address: {}
        """.format(restaurant_details['name_of_the_restaurant'] if restaurant_details['name_of_the_restaurant'] != None else "N/A",\
            restaurant_details['address_of_the_restaurant'] if restaurant_details['address_of_the_restaurant'] != None else "N/A",\
            restaurant_details['zipcode_of_the_restaurant'] if restaurant_details['zipcode_of_the_restaurant'] != None else "N/A",\
            restaurant_details['city_of_the_restaurant'] if restaurant_details['city_of_the_restaurant'] != None else "N/A",\
            restaurant_details['phone_of_the_restaurant'] if restaurant_details['phone_of_the_restaurant'] != None else "N/A",\
            restaurant_details['rating_of_the_restaurant'] if restaurant_details['rating_of_the_restaurant'] != None else "N/A",\
            restaurant_details['url_of_the_restaurant'] if restaurant_details['url_of_the_restaurant'] != None else "N/A",\
            location, date, time, cuisine, party_size, email_address)

    '''
    format(restaurant_details['name_of_the_restaurant'], restaurant_details['address_of_the_restaurant'], restaurant_details['zipcode_of_the_restaurant'], \
            restaurant_details['city_of_the_restaurant'], restaurant_details['phone_of_the_restaurant'],\
            restaurant_details['rating_of_the_restaurant'], restaurant_details['url_of_the_restaurant'],\
            location, date, time, cuisine, party_size, email_address)

    '''

    message = {"Subject":{"Data":subject},"Body":{"Html":{"Data": body}}}
    #response = client.send_email(Source = "cc.wellness.project@gmail.com", Destination = {"ToAddresses": [email_address]}, Message = message)
    response = client.send_email(Source = "cc.wellness.project@gmail.com", Destination = {"ToAddresses": ["cc.wellness.project@gmail.com"]}, Message = message)
    print("The email was sent successfully")
    


    return {
        'statusCode': 200,
        'body': json.dumps("Success!")
    }
