import boto3
import tqdm
import botocore
import string
import os 

s3 = boto3.resource('s3')
bucket = s3.Bucket('test-data-action-recorder')
bucket_prefix="2018/"
parent_dir = "output"
target_dir = os.path.join(parent_dir, "downloaded")

if not os.path.exists(parent_dir):
    os.makedirs(parent_dir)
if not os.path.exists(target_dir):
    os.makedirs(target_dir)
print("Downloading to {}".format(target_dir))

for obj in tqdm.tqdm(bucket.objects.filter(Prefix=bucket_prefix)):
    try:
        key = obj.key
        filename = key.split("/")[-1]
        if not os.path.isfile(os.path.join(target_dir, filename)):
            bucket.download_file(obj.key, os.path.join(target_dir, filename))
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise
