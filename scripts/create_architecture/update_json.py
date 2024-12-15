import json
import subnets
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
import re

def repair_json(json_str):
    # Remove trailing commas in arrays and objects
    fixed_json = re.sub(r',\s*([}\]])', r'\1', json_str)
    return fixed_json

# # # AWS credentials and region
parser = argparse.ArgumentParser()
parser.add_argument("--config-path", type=str, default="../json_configurations/default_splunk_configuration.json")

args = parser.parse_args()
config_path = args.config_path

general_parameters, common_instance_parameters, specifications_per_worker = get_architecture_parameters(config_path)

aws_region = general_parameters["aws_region"]
os.environ["AWS_DEFAULT_REGION"] = aws_region
l.info(f"Region = {aws_region}")
account_id = general_parameters["account_id"]

# # # Load the JSON data
with open('/tmp/terraform/terraform.json', 'r') as input_file:
 updated_tfvars_json = json.load(input_file)

subnets_tier1, subnets_tier2 = subnets.collecting_subnets()
# if len(subnets_tier1) >= 2:
#     # Swap the first and last elements
#     subnets_tier1[0], subnets_tier1[-1] = subnets_tier1[-1], subnets_tier1[0]

#eaf_priv_indexer_sg, eaf_priv_search_head_sg, eaf_pub_forwarder_sg, eaf_priv_splunk_host_sg, = subnets.security_group()
eaf_priv_indexer_sg, eaf_priv_search_head_sg, eaf_pub_forwarder_sg, eaf_priv_splunk_host_sg, eaf_pub_search_head_lb_sg = subnets.security_group()
print("*"*100 + "start")
print(f"eaf_priv_indexer_sg : {eaf_priv_indexer_sg} : 1")
print(f"eaf_priv_search_head_sg : {eaf_priv_search_head_sg} : 2")
print(f"eaf_pub_forwarder_sg : {eaf_pub_forwarder_sg} : 3")
print(f"eaf_priv_splunk_host_sg : {eaf_priv_splunk_host_sg} : 4")
print(f"eaf_pub_search_head_lb_sg : {eaf_pub_search_head_lb_sg} : 5")
print("*"*100 + "end")

# # # Create a dictionary to map worker types to subnets
subnet_mapping = {
    "SearchHead": subnets_tier1,
    "Indexer": subnets_tier1,
    "DeploymentServer": subnets_tier1,
    "LicenseServer": subnets_tier1,
    "Master": subnets_tier1,
    "Deploy": subnets_tier1,
    "MonitoringConsole": subnets_tier1,
    "Forwarder": subnets_tier2
 }

# # # Create a dictionary to map worker types to security groups
security_group_mapping = {
    "SearchHead": eaf_priv_search_head_sg,
    "Indexer": eaf_priv_indexer_sg,
    "DeploymentServer": eaf_priv_splunk_host_sg,
    "LicenseServer": eaf_priv_splunk_host_sg,
    "Master": eaf_priv_splunk_host_sg,
    "Deploy": eaf_priv_splunk_host_sg,
    "MonitoringConsole": eaf_priv_splunk_host_sg,
    "Forwarder": eaf_pub_forwarder_sg,
    "load_balancer" : eaf_pub_search_head_lb_sg
}

# # # Initialize counters
counter = {worker_type: 0 for worker_type in subnet_mapping.keys()}

# # # Iterate through instances and update subnets and security groups
# Iterate through instances and update subnets and security groups
for specification in updated_tfvars_json['instances_list']:
    worker_type = specification['vm_worker_type']
    if worker_type in subnet_mapping:
        if counter[worker_type] < len(subnet_mapping[worker_type]):
            specification['vm_subnet'] = subnet_mapping[worker_type][counter[worker_type]]
            counter[worker_type] += 1
    if worker_type in security_group_mapping:
        specification['vm_sg_list'] = security_group_mapping[worker_type]
updated_tfvars_json['load_balancer']['security_groups'] = security_group_mapping["load_balancer"] 

# Save the updated JSON data to a new file
with open('/tmp/terraform/terraform.tfvars.json', "w") as tfvars_file:
    json.dump(updated_tfvars_json, tfvars_file, indent=4)

print("Subnets and security groups updated and saved to '/tmp/terraform/terraform.tfvars.json'.")
with open('/tmp/terraform/terraform.tfvars.json', 'r') as file:
    tfvars_content = file.read()

# Replace single quotes with double quotes
tfvars_content = tfvars_content.replace("'", "\"")
formatted_json = json.dumps(json.loads(tfvars_content), indent=4)

with open('/tmp/terraform/terraform.tfvars.json', "w") as tfvars_file:
    json.dump(tfvars_content, tfvars_file, indent=4)

# Print the updated content


with open('/tmp/terraform/terraform.tfvars.json', 'r') as file:
    # Read the entire file content into a string
    file_content = file.read()
   
formatted_json = json.dumps(json.loads(file_content), indent=4)


try:
    data = json.loads(formatted_json)
except json.JSONDecodeError as e:
    print(f"JSON decoding error: {e}")
    # Attempt to repair the JSON
    repaired_json = repair_json(formatted_json)
    print(f"Repaired JSON: {repaired_json}")
    data = json.loads(repaired_json)


with open('/tmp/terraform/output.json', 'w',encoding='utf-8') as output_file:
    json.dump(data, output_file, indent=4)




