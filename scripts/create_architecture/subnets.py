import boto3
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
import boto3
import os
import argparse
from logging_config import logger as l

# AWS credentials and region
parser = argparse.ArgumentParser()
parser.add_argument("--config-path", type=str, default="../json_configurations/default_splunk_configuration.json")

args = parser.parse_args()
config_path = args.config_path


general_parameters, common_instance_parameters, specifications_per_worker = get_architecture_parameters(config_path)

aws_region = general_parameters["aws_region"]
os.environ["AWS_DEFAULT_REGION"] = aws_region
l.info(f"Region = {aws_region}")
account_id = general_parameters["account_id"]

tag_key = 'tier'
tag_value = 'tier1'
tag_value2 = 'tier2'
tag_key1 = 'Availability Zone'
availability_zones = [f'{aws_region}a', f'{aws_region}b', f'{aws_region}c'] 
l.info(f"availability_zones : {availability_zones}")
def collecting_subnets():
    # Create an EC2 client
    ec2 = boto3.client('ec2', region_name=aws_region)
    tier1_SubnetIds = []
    # Iterate through each availability zone in availability_zones
    for az in availability_zones:
        filters = [
            {
                'Name': f'tag:{tag_key}',
                'Values': [tag_value]
            },
            {
                'Name': 'availability-zone',
                'Values': [az]
            }
        ]

        # Describe the subnets based on the filters
        response = ec2.describe_subnets(Filters=filters)

        # Print the subnet IDs for the current availability zone
        tier1_SubnetId = [subnet['SubnetId'] for subnet in response['Subnets']]
        tier1_SubnetIds.extend(tier1_SubnetId)
    
    l.info(f"tier1_SubnetIds: {tier1_SubnetIds}") 
   
    print(f"tier1 subnets are: {tier1_SubnetIds}")

    tier2_SubnetIds = []
    # Iterate through each availability zone in availability_zones
    for az in availability_zones:
        filters = [
            {
                'Name': f'tag:{tag_key}',
                'Values': [tag_value2]
            },
            {
                'Name': 'availability-zone',
                'Values': [az]
            }
        ]

        # Describe the subnets based on the filters
        response2 = ec2.describe_subnets(Filters=filters)

        # Print the subnet IDs for the current availability zone
        tier2_SubnetId = [subnet['SubnetId'] for subnet in response2['Subnets']]
        tier2_SubnetIds.extend(tier2_SubnetId)
    print(f"tier1_SubnetIds: {tier1_SubnetIds}")
    print(f"tier2 subnets are: {tier2_SubnetIds}")
    return tier1_SubnetIds, tier2_SubnetIds

def security_group():
    # Create an EC2 client
    ec2 = boto3.client('ec2', region_name=aws_region)

    # Specify the first tag key and value you want to filter on
    tag_key1 = 'Name'
    tag_value1 = 'eaf-priv-indexer-sg'

    # Define the filters for the first security group
    filters1 = [
        {
            'Name': f'tag:{tag_key1}',
            'Values': [tag_value1]
        }
    ]

    # Describe the first security group that matches the filter
    response1 = ec2.describe_security_groups(Filters=filters1)

    # Specify the second tag key and value you want to filter on
    tag_key2 = 'Name'
    tag_value2 = 'eaf-priv-search-head-sg'

    # Define the filters for the second security group
    filters2 = [
        {
            'Name': f'tag:{tag_key2}',
            'Values': [tag_value2]
        }
    ]

    # Describe the second security group that matches the filter
    response2 = ec2.describe_security_groups(Filters=filters2)
    

    # Specify the third tag key and value you want to filter on
    tag_key3 = 'Name'
    tag_value3 = 'eaf-pub-forwarder-sg'

    # Define the filters for the third security group
    filters3 = [
        {
            'Name': f'tag:{tag_key3}',
            'Values': [tag_value3]
        }
    ]

    # Describe the third security group that matches the filter
    response3 = ec2.describe_security_groups(Filters=filters3)
    tag_key4 = 'Name'
    tag_value4 = 'eaf-priv-splunk-host-sg'
    
    filters4 = [
        {
            'Name': f'tag:{tag_key4}',
            'Values': [tag_value4]
        }
    ]

    # Describe the third security group that matches the filter
    response4 = ec2.describe_security_groups(Filters=filters4)

    tag_key5 = 'Name'
    tag_value5 = 'eaf-pub-search-head-lb-sg'

    # Define the filters for the third security group
    filters5 = [
        {
            'Name': f'tag:{tag_key5}',
            'Values': [tag_value5]
        }
    ]

    # Describe the third security group that matches the filter
    response5 = ec2.describe_security_groups(Filters=filters5)

    # Initialize lists to store security group IDs
    eaf_priv_indexer_sg = []
    eaf_priv_search_head_sg = []
    eaf_pub_forwarder_sg = []
    eaf_priv_splunk_host_sg = []
    eaf_pub_search_head_lb_sg = []

    # Process the first response
    for security_group in response1['SecurityGroups']:
        print(f"Security Group ID (eaf_priv_indexer_sg): {security_group['GroupId']}")
        eaf_priv_indexer_sg.append(security_group['GroupId'])

    # Process the second response
    for security_group in response2['SecurityGroups']:
        print(f"Security Group ID (eaf-priv-search-head-sg): {security_group['GroupId']}")
        eaf_priv_search_head_sg.append(security_group['GroupId'])

    # Process the third response
    for security_group in response3['SecurityGroups']:
        print(f"Security Group ID (eaf-pub-forwarder-sg): {security_group['GroupId']}")
        eaf_pub_forwarder_sg.append(security_group['GroupId'])

    for security_group in response4['SecurityGroups']:
        print(f"Security Group ID (eaf_priv_splunk_host_sg): {security_group['GroupId']}")
        eaf_priv_splunk_host_sg.append(security_group['GroupId'])
        
    for security_group in response5['SecurityGroups']:
        print(f"Security Group ID (eaf-pub-search-head-lb-sg): {security_group['GroupId']}")
        eaf_pub_search_head_lb_sg.append(security_group['GroupId'])

    return eaf_priv_indexer_sg, eaf_priv_search_head_sg, eaf_pub_forwarder_sg, eaf_priv_splunk_host_sg, eaf_pub_search_head_lb_sg

# Call the functions
#tier1_SubnetIds, tier2_SubnetIds = collecting_subnets()
#eaf_priv_indexer_sg, eaf_priv_search_head_sg, eaf_pub_forwarder_sg, eaf_priv_splunk_host_sg, eaf_pub_search_head_lb_sg = security_group()










       





