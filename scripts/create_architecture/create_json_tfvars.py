import json
import json

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
import copy
import time
code_mappings = {
    "environment": {
        "dev": "d",
        "test": "t",
        "prod": "p",
        # Add more mappings as needed
    },
    "instance": {
        "eu": "eu",
        "us": "us",
        # Add more mappings as needed
    },
    "product": {
        "splunk": "s",
        "other_product": "o",
        # Add more mappings as needed
    },
    "worker_type": {
        "SearchHead": "sh",
        "Indexer": "ix",
        "Forwarder": "fw",
        "LicenseServer": "ls",
        "Master": "cm",
        "Deploy": "dp",
        "DeploymentServer": "ds",
        "MonitoringConsole": "mc",
       
        # Add more mappings as needed
    }
}
parser = argparse.ArgumentParser()
parser.add_argument("--config-path", type=str, default="../json_configurations/default_splunk_configuration.json")


args = parser.parse_args()
config_path = args.config_path
config_path1 ='/tmp/terraform/terraform.json'
#config_path2 ='/tmp/terraform/terraform.json'
general_parameters, common_instance_parameters, specifications_per_worker = get_architecture_parameters(config_path)

aws_region = general_parameters["aws_region"]
os.environ["AWS_DEFAULT_REGION"] = aws_region

account_id = general_parameters["account_id"]
# Load the JSON data
with open(config_path, 'r') as input_file:
    data = json.load(input_file)

# Define the input JSON file path and output tfvars file path
input_json_file = config_path
output_tfvars_file = config_path1

instances_list = []

prefix = data["general_parameters"]["infrastructure_name_prefix"]
tags = data["common_instance_parameters"]["tags"]
print(f"tags : {tags}")
required_tages = tags['required']
print(f"required_tages : {required_tages}")
specifications = data["specifications_per_worker"]

def get_kms_id(alias_name, aws_region):
    # Initialize a KMS client
    kms_client = boto3.client('kms', region_name=aws_region)

    # List all KMS aliases
    aliases = kms_client.list_aliases()['Aliases']

    # Search for the specified alias
    for alias in aliases:
        if alias['AliasName'] == f"alias/{alias_name}":
            kms_key_id = alias['TargetKeyId']
            return kms_key_id  # Return the KMS Key ID
    return None  # Return None if alias is not found


# Create a function to generate VM names
def generate_vm_name(instance, environment, product, worker_type, count):
    print(f"instance{instance},env{environment} ,product{product} , worker_type{worker_type}")
    env_code = code_mappings["environment"].get(environment)
    instance_code = code_mappings["instance"].get(instance)
    product_code = code_mappings["product"].get(product)
    worker_type_code = code_mappings["worker_type"].get(worker_type)
    count = f"{count:03}"
    return f"{instance_code}waa-eaf{product_code}{worker_type_code}{env_code}{count}"

# Process common instance parameters
common_instance_params = data['common_instance_parameters']
common_data_volume = common_instance_params['data_volumes']



# Loop through specifications_per_worker and generate VM names
count_dict = {}
flag =0
cluster_master_count = 0

for i, spec in enumerate(specifications):
    
    environment =  tags['required']['environment']
    product = tags['required']['product']
    worker_type = spec["worker_type"]
    worker_type1 = spec["instance_type"]
    print(f"instance_type{worker_type1}")
    
    
    if worker_type not in count_dict:
        count_dict[worker_type] = 1
    else:
        count_dict[worker_type] += 1

    count = count_dict[worker_type]

    #vm_name = generate_vm_name(instance_type, environment, product, worker_type, count)
    #instance_tags = data["common_instance_parameters"]["tags"]
    instance_tags = copy.deepcopy(common_instance_params["tags"])
    updating_tags = copy.deepcopy(data["common_instance_parameters"]["tags"]['required'])
    updating_tags['type'] = worker_type
    print(f"updating_tags :{updating_tags}")
    if worker_type == "Master":
        cluster_master_count += 1
        if cluster_master_count > 1:
            updating_tags['type'] = "StandbyMaster"
            


    if "root_volume" in spec:
        root_volume = spec["root_volume"]
        root_volume['kms_key_id'] = get_kms_id('accelerator/ebs/default-encryption/key',aws_region)
        
    else:
        root_volume = common_instance_params['root_volume']
        root_volume['kms_key_id'] = get_kms_id('accelerator/ebs/default-encryption/key',aws_region)
    #updating_tags  = required_tages['type'] = worker_type
    #print(f"updating_tags : {updating_tags}")
    if aws_region == 'us-east-1':
        updating_tags['instance'] = 'us'
        updating_tags['data_residency'] = 'usa'
        updating_tags['compliance'] = 'soc1'
        data["general_parameters"]["instance_profile"]["name"] = 'eaf-instance-ssm-us-role'

    elif aws_region == 'eu-central-1':
        updating_tags['instance'] = 'eu'
        updating_tags['data_residency'] = 'eea'
        updating_tags['compliance'] = 'soc1-gdpr'
        data["general_parameters"]["instance_profile"]["name"] = 'eaf-instance-ssm-eu-role'
    elif aws_region == 'eu-west-2':
        updating_tags['instance'] = 'uk'
        updating_tags['data_residency'] = 'eea'
        updating_tags['compliance'] = 'soc1-gdpr'
        data["general_parameters"]["instance_profile"]["name"] = 'eaf-instance-ssm-uk-role'
    instance_type = updating_tags['instance']
    vm_name = generate_vm_name(instance_type, environment, product, worker_type, count)



    
    instance = {
        "vm_instance_type": worker_type1,
        "vm_ami_name": common_instance_params['ami_name'],
        "vm_instance_profile": data["general_parameters"]["instance_profile"]["name"],
        "vm_worker_type": worker_type,
        "vm_sg_list": "<Replace with Security Group ID>",  # Replace with actual SG ID
        "vm_tags": updating_tags,
        "vm_subnet": "<Replace with Subnet ID>",  # Replace with actual Subnet ID
        "vm_name": vm_name,
        "root_volume": root_volume,
        "data_volumes": {},
    }
   
   
    load_balancer = {
         "tags": required_tages,
         "security_groups": "<Replace with Security Group ID>",
         "names" : create_lb_names(general_parameters)
    }
    

    
    

    # Add data volumes if available
    #instance["data_volumes"].update(common_data_volume)
    for common_data_volume in common_instance_params['data_volumes']:
        # Clone the common data volume to avoid modifying the original common data volume
        new_data_volume = common_data_volume.copy()
        # Define a unique device name for the common data volume (you can adjust this if needed)
        common_data_volume_device_name = f"/dev/xvd{chr(ord('f') )}"
        instance["data_volumes"][common_data_volume_device_name] = new_data_volume
        new_data_volume['kms_key_id'] = get_kms_id('accelerator/ebs/default-encryption/key',aws_region)
    if "data_volumes" in spec:
        for j, data_volume in enumerate(spec["data_volumes"], start=6):
            data_volume_device_name = f"/dev/xvd{chr(ord('g') )}"
            instance["data_volumes"][data_volume_device_name] = data_volume
            data_volume['kms_key_id'] = get_kms_id('accelerator/ebs/default-encryption/key',aws_region)

    # Append the instance to the list
    
    instances_list.append(instance)
    

# Construct the tfvars dictionary
tfvars_data = {
    "aws_region": data["general_parameters"]["aws_region"],
    "account_id": data["general_parameters"]["account_id"],
    "kms_key_id": get_kms_id('accelerator/ebs/default-encryption/key',aws_region), 
    "instances_list": instances_list,
    "load_balancer" :  load_balancer
}


# Convert the tfvars data to a JSON string with indentation for readability
tfvars_json = json.dumps(tfvars_data, indent=4)



# Print or save the tfvars JSON data
# If you want to save it to a file, you can use the following code:
if not os.path.exists(os.path.dirname(config_path1)):
    os.makedirs(os.path.dirname(config_path1))

with open(config_path1, 'w') as tfvars_file:
    tfvars_file.write(tfvars_json)



print("********************************end*******************************************")
#This code uses the provided code mappings to generate VM names based on the specified format. Replace the placeholders for Security Group ID, Subnet ID, and KMS Key ID with actual values from your AWS environment.







