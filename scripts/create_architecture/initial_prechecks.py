import boto3
from botocore.exceptions import ClientError
import json
import argparse
from logging_config import logger as l
from cloudformation import *
from stack_utils import *
from security_groups import manage_security_groups
import os
from dictionary_utils import *
from collections import defaultdict
import copy
import time
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--config-path", type=str, default="../json_configurations/default_splunk_configuration.json")
args = parser.parse_args()
config_path = args.config_path
general_parameters, common_instance_parameters, specifications_per_worker = get_architecture_parameters(config_path)

aws_region = general_parameters["aws_region"]
os.environ["AWS_DEFAULT_REGION"] = aws_region

account_id = general_parameters["account_id"]
bucket_name = 'terraform-state-'+account_id+'-'+aws_region
table_name = 'terraform-state-lock-'+account_id+'-'+aws_region
instance_profile_name = 'ec2-instance-access'


def is_instance_profile_exists(instance_profile_name):
    iam = boto3.client('iam')

    try:
        iam.get_instance_profile(InstanceProfileName=instance_profile_name)
        return True
    except iam.exceptions.NoSuchEntityException:
        return False
    
def is_table_exists(table_name):
    dynamodb = boto3.client('dynamodb')

    try:
        dynamodb.describe_table(TableName=table_name)
        return True
    except dynamodb.exceptions.ResourceNotFoundException:
        return False

def check_bucket_availability(bucket_name):
    # Create an S3 client with the provided credentials and region
    s3 = boto3.client('s3')

    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"The bucket '{bucket_name}' exists and is accessible. Continuing with the program.")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"The bucket '{bucket_name}' does not exist. Continuing with the program.")
            return False
        elif error_code == '403':
            print(f"You do not have permission to access the bucket '{bucket_name}'. Exiting the program.")
            sys.exit(1)
        else:
            print(f"An error occurred while checking the bucket '{bucket_name}': {e}")
            sys.exit(1)




def is_ipam_pool_available():
    # Create a boto3 client for the EC2 service
    ec2_client = boto3.client('ec2')

    # List all the managed prefix lists
    response = ec2_client.describe_ipam_pools()
    print("Response:", response)

    ipam_pools = response.get('IpamPools', [])
    ipam_pool_ids = [pool['IpamPoolId'] for pool in ipam_pools]
    print(f"ipam_pool_ids : {ipam_pool_ids}")

    # Check if there are any IPAM pools
    if ipam_pool_ids:
        print("ipam_pool_ids is present")
        return True
    else:
        print("ipam_pool_ids is empty")
        return False
  
if all([
    
    check_bucket_availability(bucket_name),
    is_table_exists(table_name),
    is_ipam_pool_available()
    
    
]):
    print("All checks passed. Continuing with the program.")
else:
    print("One or more checks failed. Exiting the program.")
    sys.exit(1)
