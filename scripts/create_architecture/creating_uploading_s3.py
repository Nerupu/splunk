import os
import wget
import boto3
import argparse
from logging_config import logger as l
from cloudformation import *
from stack_utils import *
from security_groups import manage_security_groups
import os
import argparse
from logging_config import logger as l
from dictionary_utils import *
from collections import defaultdict
import time

# AWS credentials and region
parser = argparse.ArgumentParser()
parser.add_argument("--config-path", type=str, default="../json_configurations/default_splunk_configuration.json")

args = parser.parse_args()
config_path = args.config_path
parser.add_argument("--config-path1", type=str, default="../create_architecture/inputs.conf")

args = parser.parse_args()
config_path1 = args.config_path1


general_parameters, common_instance_parameters, specifications_per_worker = get_architecture_parameters(config_path)

aws_region = general_parameters["aws_region"]
os.environ["AWS_DEFAULT_REGION"] = aws_region
l.info(f"Region = {aws_region}")
print((f"Region = {aws_region}"))
account_id = general_parameters["account_id"]

#account_id = 'prasad_eaf_testing'


# Define the URL to download the Splunk RPM
rpm_url = "https://download.splunk.com/products/splunk/releases/9.1.1/linux/splunk-9.1.1-64e843ea36b1.x86_64.rpm"

# Define the local and S3 paths for the RPM file
local_directory = "/tmp/splunk"  # Specify the local directory
local_rpm_path = os.path.join(local_directory, "splunk-9.1.1-64e843ea36b1.x86_64.rpm")
s3_bucket_name = 'eaf-splunk-binaries-' + account_id + '-' + aws_region
s3_key = "splunk/binary/splunk-9.1.1-64e843ea36b1.x86_64.rpm"
local_input_conf_path = "./script/iputs.conf"
bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowSSLRequestsOnly",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                f"arn:aws:s3:::{s3_bucket_name}/*",
                f"arn:aws:s3:::{s3_bucket_name}"
            ],
            "Condition": {
                "Bool": {
                    "aws:SecureTransport": "false"
                }
            }
        }
    ]
}

bucket_policy = json.dumps(bucket_policy)

# Initialize S3 client

s3 = boto3.client('s3',region_name=aws_region)

# Check if the S3 bucket already exists, and if not, create it
bucket_exists = False
try:
    s3.head_bucket(Bucket=s3_bucket_name)
    bucket_exists = True
except Exception as e:
    if '404' in str(e):
        # Bucket does not exist, create it
        if aws_region == 'us-east-1':
            s3.create_bucket(Bucket=s3_bucket_name)
            print(f"S3 bucket '{s3_bucket_name}' created.")
            time.sleep(30)
            s3.put_bucket_policy(Bucket=s3_bucket_name, Policy=bucket_policy)
            bucket_exists = True
        else:
            s3.create_bucket(Bucket=s3_bucket_name,CreateBucketConfiguration={ 'LocationConstraint': aws_region})
            print(f"S3 bucket '{s3_bucket_name}' created.")
            time.sleep(30)
            s3.put_bucket_policy(Bucket=s3_bucket_name, Policy=bucket_policy)
            bucket_exists = True



    else:
        raise

# Create the local directory if it doesn't exist
if not os.path.exists(local_directory):
    os.makedirs(local_directory)

if bucket_exists:
    # Check if the file already exists in S3
    response = s3.list_objects(Bucket=s3_bucket_name, Prefix=s3_key)

    if 'Contents' in response:
        print("RPM file already exists in S3. No need to download and upload.")
    else:
        # Download the RPM file from the specified URL
        wget.download(rpm_url, local_rpm_path)
    
        # Upload the RPM file to S3
        s3.upload_file(local_rpm_path, s3_bucket_name, s3_key)
        print("RPM file uploaded to S3.")
        s3_input_conf_key = "splunk/deploymentServer/default_app/v1/inputs.conf"  # Specify the S3 key for input.conf
        s3.upload_file(config_path1, s3_bucket_name, s3_input_conf_key)
        print("input.conf file uploaded to S3.")

env_file = os.getenv("GITHUB_ENV")
print(f"env_file : {env_file}")
if env_file is not None:
    with open(env_file, "a+") as env:
        l.info("Current content of github env file")
        l.info(env.read())

        env.write(f"AWS_REGION={general_parameters['aws_region']}\n")
        env.write(f"S3_BUCKET_NAME={s3_bucket_name}\n")
       


    with open(env_file, "r") as env:
        l.info("Updated content of github env file")
        l.info(env.read())

