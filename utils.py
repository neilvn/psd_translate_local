import boto3
import json


def get_s3_item(bucket_name, key):
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket_name=bucket_name, key=key)
    file_content = obj.get()['Body'].read().decode('utf-8')
    json_content = json.loads(file_content)
    return json_content
