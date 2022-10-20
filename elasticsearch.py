import boto3
from variables import * 
import requests
import csv

endpoint = 'https://search-restaurants-4zjgqhcwbcndtzuuiuzkm7aqoa.us-east-1.es.amazonaws.com/' 
subpath = 'restaurants/restaurants' 
reg = 'us-east-1' 

service = 'es'

elastic_search_url = endpoint + subpath

with open('restaurants_dynamodbdata.csv', encoding='utf-8', newline='') as file:
    data=csv.reader(file)
    restaurant_data=list(data)
restaurant_data=restaurant_data[1:]

for restaurant in restaurant_data:
    index_data={'restaurant_id': restaurant[0],'cuisine': restaurant[2]}
    requests.post(elastic_search_url, auth=("cloud1", "nigel@CLOUD1"), json=index_data)