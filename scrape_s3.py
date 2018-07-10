import boto3
import botocore
import string

s3 = boto3.resource('s3')
bucket = s3.Bucket('deepmine-alpha-data')
bucket_prefix="2018/07"

for obj in bucket.objects.filter(Prefix=bucket_prefix):
    print (obj)
    try:
        key = obj.key
        filename = key.split("/")[-1]
        bucket.download_file(obj.key, filename)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise
