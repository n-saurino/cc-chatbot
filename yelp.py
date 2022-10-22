#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 13 19:07:50 2022

@author: harsh
"""

import requests
import json
import os
import boto3
from botocore.exceptions import ClientError
import datetime,time
from decimal import Decimal

def scrape_and_store(api, api_key, cuisine_type, location):
    #count=0
    #file=open(cuisine_type+".txt",'w')
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('yelp-restaurants')
    offset=0
    headers= {"Authorization": "Bearer " + api_key}
    for i in range(18):
        offset+=50
        parameters = {'term': 'restaurant','location': location,
            'radius': 40000,'categories': cuisine_type, #25 miles/40000 meters is the maximum cap
            'limit': 50,'offset': offset,
            'sort_by': 'best_match'
        }
        response_businesses=requests.get(api,parameters,headers=headers).json()
        # count=count+len(response_businesses['businesses'])
        # print(count)
        #file.write(json.dumps(response_businesses)+"\n\nsure\n"+cuisine_type+"\n")
        for business in response_businesses['businesses']:
            try:
                table.put_item(
                    Item={
                        'businessId': business['id'],
                        'name': business['name'],
                        'category': business['categories'][0]['alias'],
                        'address': business['location']['address1'],
                        'Latitude':Decimal(str(business['coordinates']['latitude'])),
                        'Longitude':Decimal(str(business['coordinates']['longitude'])),
                        'city': business['location']['city'],
                        'zipcode': business['location']['zip_code'],
                        'reviewCount': business['review_count'],
                        'rating': Decimal(str(business['rating'])),
                        'phone': business['phone'],
                        'url': str(business['url']),
                        'insertedAtTimestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
            except ClientError as e:
                print(e.response['Error']['Code'])
    #file.close()
    return True

if __name__=='__main__':
    api_key = "gEZG02DJzLjuEiEAMIjrfX5Cl7GzmBbDm_RnyFvzTrUZsOLFQMyoX0FRn_3hgLlMDB9LblVMJcP4EXIjwv2lH44GvMo9qNZrFah4n63T0zpAgHhFvDU9qK0_Mp1IY3Yx"
    api="https://api.yelp.com/v3/businesses/search"
    client = boto3.client('dynamodb', region_name='us-east-1')

    try:
        resp = client.create_table(
        TableName="yelp-restaurants",
        
        KeySchema=[
            {
                "AttributeName": "businessId",
                "KeyType": "HASH"
            }
        ],
        AttributeDefinitions=[
            {"AttributeName": "businessId","AttributeType": "S"}
            
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 1,
            "WriteCapacityUnits": 1
        }
    )
        print("Table created successfully!")
    except Exception as e:
        print("Error creating table:")
        print(e)
    time.sleep(10) 
    """Adding delay to give enough time for the table to be initialized
    before the table is accessed by the function"""
    cuisine_list=["american","indpak","italian","japanese","chinese"]
    location=["Manhattan","Bronx","Brooklyn"]
    for cuisine in cuisine_list:
        scrape_and_store(api,api_key,cuisine,location)
    