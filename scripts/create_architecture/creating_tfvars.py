import os
import json
from cloudformation import *
from stack_utils import *
from security_groups import manage_security_groups
import os
import argparse
from logging_config import logger as l
from dictionary_utils import *
from collections import defaultdict

input_file_path = r'C:\My Project work\POCs\linux Patching\windows_precheck\learning\keys\SRE_TEAM\prasad\vault_automation\EAF\EAF-Splunk-WIP\scripts\json_configurations\default_splunk_configuration.json'

def get_architecture_parameters(input_file_path):
    if not os.path.isfile(input_file_path):
        raise Exception(f"File {input_file_path} does not exist. Error while looking for the architecture configuration file.")

    with open(input_file_path, "r") as input_file:
        config_content = json.load(input_file)
    
    general_parameters = config_content.get("general_parameters", None)
    common_instance_parameters = config_content.get("common_instance_parameters", None)
    specifications_per_worker = config_content.get("specifications_per_worker", None)
    
    return general_parameters, common_instance_parameters, specifications_per_worker
    
general_parameters, common_instance_parameters, specifications_per_worker = get_architecture_parameters(input_file_path)
print(general_parameters)


instances_list = []
vm_types_count = defaultdict(int)

for worker_specification in specifications_per_worker:
    worker_dict = {}
    worker_dict['vm_instance_type'] = get_from_dict_with_check(worker_specification, common_instance_parameters, 'instance_type')
    # worker_dict['vm_ami_name'] = 'ami-0a6006bac3b9bb8d3' #TODO: Create dynamic ami filtr to search for CCP AMI
    worker_dict['vm_ami_name'] = get_from_dict_with_check(worker_specification, common_instance_parameters, 'ami_name')
    worker_dict['vm_instance_profile'] = instance_profile_name


    # worker_dict['vm_sg_list'] = get_from_dict_with_check(worker_specification, common_parameters, 'security_groups')
    # worker_dict['vm_sg_list'] = list(set(worker_dict['vm_sg_list']))
    ## WORKER TYPE
    worker_dict['vm_worker_type'] = get_worker_type(
        worker_specification, 
        common_instance_parameters, 
        supported_types = all_security_groups)


    # WORKER SECURITY GROUPS
    worker_dict['vm_sg_list'] = [security_groups_logical_to_id[worker_dict['vm_worker_type']]]

    ## TAGS
    worker_dict['vm_tags'] = get_tags(worker_specification, common_instance_parameters)

    ## SUBNET
    worker_dict['vm_subnet'] = subnet_dispenser.next(worker_dict['vm_worker_type'])
    
    ## NAME
    # dependant on 'vm_tags', 'vm_worker_type'  from worker_dict
    worker_dict['vm_name'] = create_vm_name(worker_dict, aws_region, vm_types_count)

    ## VOLUMES, root has to be set, data volumes are optional
    worker_dict = manage_volumes(worker_specification, common_instance_parameters, worker_dict)

  

    instances_list.append(worker_dict)

terraform_dict = dict()
#aws region, account_id, kms_key_id, rds_config, instances_list
terraform_dict['aws_region'] = general_parameters['aws_region']
terraform_dict['account_id'] = general_parameters['account_id']
terraform_dict['kms_key_id'] = get_resource_from_list('AWS::KMS::Key', list_of_resources) if get_resource_from_list('AWS::KMS::Key', list_of_resources) is not None else kms_key_id
terraform_dict['instances_list'] = instances_list




terraform_dict['load_balancer'] = general_parameters['load_balancer']
terraform_dict['load_balancer']['security_groups'] = [security_groups_logical_to_id['ApplicationLoadBalancer']]
terraform_dict['load_balancer']['names'] = create_lb_names(general_parameters)



with open('../../terraform/terraform.tfvars.json', "w") as tfvars:
    json.dump(terraform_dict, tfvars, indent=4)
