import json
import argparse
import os
import logging
from pprint import pprint as pp
from collections import defaultdict
from dictionary_utils import *

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s -- %(message)s')
logger.setLevel(logging.INFO)

argparser = argparse.ArgumentParser()

argparser.add_argument('--workflow-config', dest='workflow_config', required=True, help='Workflow config file in json format')
argparser.add_argument('--security-groups-mapping', dest='sg_mapping', required=True, help='Security group mapping file in json format')
argparser.add_argument('--dev', dest='dev', action='store_true', help='Run in dev mode', default=False)

args = argparser.parse_args()

env_file = os.getenv("GITHUB_ENV")

with open(args.workflow_config) as f:
    content = f.read()

    workflow_config = json.loads(content) if is_valid_json(content) else None
    # try:
    #     workflow_config['common_instance_parameters']['security_groups'] = list(map( lambda x: str(x.replace('[','').replace(']', '').replace('\n', '').replace(' ','').replace('\"','')) ,workflow_config['common_instance_parameters']['security_groups'].split(",")))
    # except KeyError as ke:
    #     logger.warning("No security groups defined in workflow config")
    #     workflow_config['common_instance_parameters']['security_groups'] = []
    # except Exception as e:
    #     logger.error("Error while parsing security groups")
    #     raise e


    if workflow_config:
        logger.info("Workflow config is valid json")
    else:
        logger.info("Workflow config is not valid json")
        raise Exception("Workflow config is not valid json")

if not args.dev and env_file is None:
    raise Exception("GITHUB_ENV is not set")
elif not args.dev:
    with open(env_file, "a+") as env:
        logger.info("Current content of github env file")
        logger.info(env.read())

        env.write(f"AWS_REGION={workflow_config['general_parameters']['aws_region']}\n")
        env.write(f"S3_BUCKET_NAME={workflow_config['general_parameters']['s3_bucket_name']}\n")


    with open(env_file, "r") as env:
        logger.info("Updated content of github env file")
        logger.info(env.read())

with open(args.sg_mapping) as f:
    content = f.read()

    sg_mapping = json.loads(content) if is_valid_json(content) else None

    if sg_mapping:
        logger.info("Security group mapping is valid json")
    else:
        logger.info("Security group mapping is not valid json")
        raise Exception("Security group mapping is not valid json")

common_parameters = get_common_parameters(workflow_config['common_instance_parameters'])

check_key(workflow_config, 'general_parameters')
check_key(workflow_config, 'specifications_per_worker')


inputs_dict = {}

inputs_dict['aws_region'] = workflow_config['general_parameters']['aws_region']
inputs_dict['account_id'] = workflow_config['general_parameters']['account_id']
inputs_dict['load_balancer'] = workflow_config['general_parameters']['load_balancer']
inputs_dict['load_balancer']['security_groups'] = [sg_mapping['application_load_balancer_sg_id']]
inputs_dict['load_balancer']['names'] = create_lb_names(inputs_dict)

try:
    instances_quantity = int(check_key(workflow_config['general_parameters'], 'instances_quantity'))
except ValueError:
    raise Exception("instances_quantity must be an integer")

if instances_quantity != len(workflow_config['specifications_per_worker']):
    raise Exception(f"instances_quantity must be equal to the number of specifications_per_worker. Currently you defined {instances_quantity} instances but provided {len(workflow_config['specifications_per_worker'])}. You have to define specifications for each instance, but you can provide empty dicttionary for some of them. Read the documentation for more details.")




subnets = [common_parameters['subnet_az1'], common_parameters['subnet_az2'], common_parameters['subnet_az3']]
all_worker_types = list(set(map(lambda x: x['worker_type'], workflow_config['specifications_per_worker'])))

subnet_dispenser = SubnetDispenser(all_worker_types=all_worker_types, subnets=subnets)


inputs_dict['instances_list'] = []
vm_types_count = defaultdict(int)

for worker_specification in workflow_config['specifications_per_worker']:
    worker_dict = {}
    worker_dict['vm_instance_type'] = get_from_dict_with_check(worker_specification, common_parameters, 'instance_type')
    worker_dict['vm_ami_name'] = get_from_dict_with_check(worker_specification, common_parameters, 'ami_name')
    instance_profile = get_from_dict_with_check(worker_specification, common_parameters, 'instance_profile')
    worker_dict['vm_instance_profile'] = check_key(instance_profile, 'name')


    # worker_dict['vm_sg_list'] = get_from_dict_with_check(worker_specification, common_parameters, 'security_groups')
    # worker_dict['vm_sg_list'] = list(set(worker_dict['vm_sg_list']))
    ## WORKER TYPE
    worker_dict['vm_worker_type'] = get_worker_type(worker_specification, common_parameters)


    # WORKER SECURITY GROUPS
    worker_dict['vm_sg_list'] = get_security_groups(worker_dict['vm_worker_type'], sg_mapping)

    ## TAGS
    worker_dict['vm_tags'] = get_tags(worker_specification, common_parameters)

    ## SUBNET
    worker_dict['vm_subnet'] = subnet_dispenser.next(worker_dict['vm_worker_type'])
    
    ## NAME
    # dependant on 'vm_tags', 'vm_worker_type'  from worker_dict
    worker_dict['vm_name'] = create_vm_name(worker_dict, inputs_dict['aws_region'], vm_types_count)

    ## VOLUMES, root has to be set, data volumes are optional
    worker_dict = manage_volumes(worker_specification, common_parameters, worker_dict)
    
    

    
    inputs_dict['instances_list'].append(worker_dict)



pp(inputs_dict)

with open('../../terraform/terraform.tfvars.json', "w") as tfvars:
    json.dump(inputs_dict, tfvars, indent=4)