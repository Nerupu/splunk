import boto3, logging
import yaml, string
import concurrent.futures
from pprint import pprint
from vpc_utils import vpc_exists
from sg_config import configure_inbound_and_outbound_rules
from utils import validate_template, wait_until_stack_is_created_and_get_outputs
import json
"""
Parses a port range string into a tuple of integers.
"""
def parse_port_range(port_range):
    if '-' in port_range:
        start, end = port_range.split('-')
        return (int(start), int(end))
    else:
        return (int(port_range), int(port_range))



"""
Generates a list of security group rules based on a list of port ranges and a CIDR IP.
"""
def generate_security_group_rules(port_ranges, cidr_ip):
    rules = []
    for port_range in port_ranges:
        start, end = parse_port_range(port_range)
        protocol = 'tcp'
        rule = {
            'IpProtocol': protocol,
            'FromPort': start,
            'ToPort': end,
            'CidrIp': cidr_ip
        }
        # rule = f'{protocol},{start},{end},{cidr_ip}'
        rules.append(rule)
    return rules

def get_security_group_id_given_name(
        vpc_id:str, 
        group_name:str, 
        l:logging.Logger = logging.getLogger(__name__)
        ):
    ec2 = boto3.resource('ec2')

    if vpc_exists(vpc_id):
        vpc = ec2.Vpc(vpc_id)
        l.info(f"Looking for security group {group_name} in VPC {vpc_id}...")
        for security_group in vpc.security_groups.all():
            l.info(f"Security group: {security_group.group_name} ({security_group.id})")
            if security_group.group_name == group_name or security_group.id == group_name:
                return security_group.id
        return None
    else:
        raise Exception(f"VPC {vpc_id} does not exist")

def security_group_exists_given_id(
        vpc_id:str, 
        sg_id:str, 
        l:logging.Logger = logging.getLogger(__name__)
        ):
    ec2 = boto3.resource('ec2')

    if vpc_exists(vpc_id):
        vpc = ec2.Vpc(vpc_id)
        l.info(f"Looking for security group {sg_id} in VPC {vpc_id}...")
        for security_group in vpc.security_groups.all():
            l.info(f"Security group: {security_group.group_name} ({security_group.id})")
            if security_group.id == sg_id:
                return True
        return False
    else:
        raise Exception(f"VPC {vpc_id} does not exist")



def parse_sg_template(
        pre_template_name: str = 'cf_sg_template.yaml', 
        template_name:str = 'cf_sg.yaml',
        rules: list = None, 
        l: logging.Logger = logging.getLogger(__name__)
        ) -> None:
    with open(pre_template_name, 'r') as f:
        template_body = string.Template(f.read())
    
    indent = "  " * 4

    #Convert the rules to a string in yaml format
    yaml_rules = yaml.dump(rules, default_flow_style=False)
    yaml_rules = yaml_rules.splitlines()
    yaml_rules = [indent + line for line in yaml_rules]
    yaml_rules = '\n'.join(yaml_rules)
    
    #Replace the rules in the template with the generated rules
    yaml_str = template_body.substitute(ingress_rules=yaml_rules)


    l.debug(f"Generated yaml string:")
    l.debug("")
    pprint(yaml_str) if l.level == logging.DEBUG else None    


    with open(template_name, 'w') as f:
        f.write(yaml_str)

def create_security_group(
        vpc_id, 
        stack_name:str, 
        security_group_name:str = "EAF-SG", 
        description:str = 'Security Group for EAF splunk infrastructure', 
        ports: str = '22,8000,9777,8089,8191,9997,9887,433,80,443', 
        inbound_cidr_ip:str ='0.0.0.0/0', 
        template_name:str = 'cf_sg.yaml', 
        group_id:str = None,
        delete_if_failed:bool = True, 
        l:logging.Logger = logging.getLogger(__name__)
        ) -> str:


    if not vpc_exists(vpc_id):
        raise Exception(f"VPC {vpc_id} does not exist")

    sg_id = get_security_group_id_given_name(vpc_id, security_group_name)

    if sg_id:
        l.info(f"Security group {security_group_name} already exists in VPC {vpc_id}")
        return sg_id
    
    if security_group_exists_given_id(vpc_id, group_id):
        l.info(f"Security group {group_id} already exists in VPC {vpc_id}")
        return group_id

    if security_group_name.startswith('sg-'):
        l.warning(f"Security group name {security_group_name} starts with sg-*, this is not allowed by AWS, defaulting to 'EAF-SG'")
        security_group_name = 'EAF-SG'

    sg_id = check_if_sg_with_ports_exists(vpc_id, ports)
    if sg_id:
        l.info(f"Security group with ports {ports} already exists in VPC {vpc_id}")
        return sg_id

    # Generate the list of security group rules based on the input port ranges
    port_ranges = ports.split(',')
    if '443' not in port_ranges:
        raise Exception(f"Port 443 is required for the security group, please add it to the list of ports")
    rules = generate_security_group_rules(port_ranges, inbound_cidr_ip)

    #check if the security group allows inbound traffic on port 443

    l.info(f"Creating security group {security_group_name} in VPC {vpc_id} with description \'{description}\' and rules:")
    l.info("")
    for rule in rules:
        l.info(rule)
    l.info("")

    parse_sg_template(rules=rules, pre_template_name='cf_sg_template.yaml', template_name=template_name)

    template_body = validate_template(template_name)

    if l.level == logging.DEBUG:
        print(f"Json dump: {json.dumps(rules)}") 
        print(f"joined list: {';'.join(rules)}") if type(rules) == str else None

    cloudformation_client = boto3.client('cloudformation')

    response = cloudformation_client.create_stack(
        StackName=stack_name,
        TemplateBody=template_body,
        Parameters=[
            {
                'ParameterKey': 'GroupName',
                'ParameterValue': security_group_name
            },
            {
                'ParameterKey': 'VpcId',
                'ParameterValue': vpc_id
            },
            {
                'ParameterKey': 'Description',
                'ParameterValue': description
            }
        ],
        Capabilities=['CAPABILITY_IAM']
    )

    l.debug("Response from cloudformation:")
    l.debug(response)
    l.debug("")

    # Wait until the stack is created
    stack_outputs = wait_until_stack_is_created_and_get_outputs(stack_name, delete_if_failed=delete_if_failed)

    sg_id = stack_outputs['SecurityGroupId']

    return sg_id

from copy import copy

def check_if_sg_with_ports_exists(
        vpc_id: str, 
        ports: str):
    ec2 = boto3.client('ec2')
    if type(ports) != str:
        raise Exception(f"Ports must be a comma separated string of port numbers. Received {type(ports)}")
    ports = list(map(int, ports.split(',')))
    if vpc_exists(vpc_id):
        response = ec2.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        security_groups = response['SecurityGroups']
        # print(security_groups)
        for security_group in security_groups:

            valid_sg_ports = [
                ip_permission['FromPort'] for ip_permission in security_group['IpPermissions'] 
                if ip_permission['IpProtocol'] != '-1' and ip_permission['FromPort'] == ip_permission['ToPort']
                ]


            if all([port in valid_sg_ports for port in ports]) and len(valid_sg_ports) == len(ports):
                return security_group['GroupId']
        return None

def lookup_sg_by_names(vpc_id, sg_name_to_id:map, l:logging.Logger = logging.getLogger(__name__)):
    ec2 = boto3.client('ec2')
    response = ec2.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    security_groups = response['SecurityGroups']
    sg_names = sg_name_to_id.keys()
    
    for sg_name in sg_names:
        l.info(f"Looking for security group {sg_name} in VPC {vpc_id}... ", extra={'ending': ''})
        from pprint import pprint
        for security_group in security_groups:
            # pprint(security_group)
            if security_group['GroupName'] == sg_name:
                l.info(f"Found!")
                sg_name_to_id[sg_name]=security_group['GroupId']
        if not sg_name_to_id[sg_name]:
            l.info(f"Not found.")

    return sg_name_to_id

def get_cidr(subnet):
    ec2 = boto3.client('ec2')
    response = ec2.describe_subnets(SubnetIds=[subnet])
    return response['Subnets'][0]['CidrBlock']


def get_subnets_cidrs(subnets, l=logging.getLogger(__name__)):
    subnet_cidrs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_subnet = {executor.submit(get_cidr, subnet): subnet for subnet in subnets}
        for future in concurrent.futures.as_completed(future_to_subnet):
            subnet = future_to_subnet[future]
            try:
                data = future.result()
            except Exception as exc:
                l.error(f"Error getting CIDR for subnet {subnet}: {exc}")
            else:
                subnet_cidrs.append(data)

    return subnet_cidrs

def create_all_security_groups(
    vpc_id, 
    stack_name:str,
    application_load_balancer_sg_name:str,
    search_head_sg_name:str,
    heavy_forwarder_sg_name:str,
    deploy_sg_name:str,
    indexer_sg_name:str,
    deployment_server_sg_name:str,
    master_cluster_node_sg_name:str,
    license_server_sg_name:str,
    aws_services_sg_name:str,
    access_to_load_balancer_sg_id:str,
    private_subnets:list,
    provision_jumphost_sg_group:bool,
    template_name:str = 'cf_sg2.yaml', 
    l:logging.Logger = logging.getLogger(__name__)
):
    if not vpc_exists(vpc_id):
        raise Exception(f"VPC {vpc_id} does not exist")
    
    sg_name_to_id = {
        application_load_balancer_sg_name: None,
        search_head_sg_name: None,
        heavy_forwarder_sg_name: None,
        deploy_sg_name: None,
        indexer_sg_name: None,
        deployment_server_sg_name: None,
        master_cluster_node_sg_name: None,
        license_server_sg_name: None,
        aws_services_sg_name: None
    }

    sg_role_to_id = {
        'application_load_balancer_sg_id': None,
        'search_head_sg_id': None,
        'heavy_forwarder_sg_id': None,
        'deploy_sg_id': None,
        'indexer_sg_id': None,
        'deployment_server_sg_id': None,
        'master_cluster_node_sg_id': None,
        'license_server_sg_id': None,
        'aws_services_sg_id': None
    }


    
    l.info(f"Looking up security groups in VPC {vpc_id}")
    l.info("")
    sg_name_to_id = lookup_sg_by_names(vpc_id, sg_name_to_id, l)

    if all(sg_name_to_id.values()):
        l.info("All security groups already exist, skipping creation")
        sg_role_to_id['application_load_balancer_sg_id'] = sg_name_to_id[application_load_balancer_sg_name]
        sg_role_to_id['search_head_sg_id'] = sg_name_to_id[search_head_sg_name]
        sg_role_to_id['heavy_forwarder_sg_id'] = sg_name_to_id[heavy_forwarder_sg_name]
        sg_role_to_id['deploy_sg_id'] = sg_name_to_id[deploy_sg_name]
        sg_role_to_id['indexer_sg_id'] = sg_name_to_id[indexer_sg_name]
        sg_role_to_id['deployment_server_sg_id'] = sg_name_to_id[deployment_server_sg_name]
        sg_role_to_id['master_cluster_node_sg_id'] = sg_name_to_id[master_cluster_node_sg_name]
        sg_role_to_id['license_server_sg_id'] = sg_name_to_id[license_server_sg_name]
        sg_role_to_id['aws_services_sg_id'] = sg_name_to_id[aws_services_sg_name]

        return sg_role_to_id

    #check if only some of the groups exist
    if any([sg_name_to_id[sg_name] != None for sg_name in sg_name_to_id]):
        l.error("Some security groups exist with given names. Make sure that provided names are unique and try again")
        raise Exception("Some security groups exist with given names. Make sure that provided names are unique and try again")
    

    #check if all of the groups are None
    if all([sg_name_to_id[sg_name] == None for sg_name in sg_name_to_id]):
        l.info("No security groups exist, creating all of them")
    
    template_body = validate_template(template_name)

    l.info("Getting CIDRs for private subnets")
    l.info("")

    private_subnets_cidrs = get_subnets_cidrs(private_subnets, l)

    l.info("Creating security groups with following names:")
    l.info(f"Application Load Balancer: {application_load_balancer_sg_name}")
    l.info(f"Search Head: {search_head_sg_name}")
    l.info(f"Heavy Forwarder: {heavy_forwarder_sg_name}")
    l.info(f"Deploy: {deploy_sg_name}")
    l.info(f"Indexer: {indexer_sg_name}")
    l.info(f"Deployment Server: {deployment_server_sg_name}")
    l.info(f"Master Cluster Node: {master_cluster_node_sg_name}")
    l.info(f"License Server: {license_server_sg_name}")
    l.info(f"AWS Services: {aws_services_sg_name}")
    l.info("")



    cloudformation_client = boto3.client('cloudformation')

    response = cloudformation_client.create_stack(
        StackName=stack_name,
        TemplateBody=template_body,
        Parameters=[
            {
                'ParameterKey': 'VpcId',
                'ParameterValue': vpc_id
            },
            {
                'ParameterKey': 'ApplicationLoadBalancerSGName',
                'ParameterValue': application_load_balancer_sg_name
            },
            {
                'ParameterKey': 'SearchHeadSGName',
                'ParameterValue': search_head_sg_name
            },
            {
                'ParameterKey': 'HeavyForwarderSGName',
                'ParameterValue': heavy_forwarder_sg_name
            },
            {
                'ParameterKey': 'DeploySGName',
                'ParameterValue': deploy_sg_name
            },
            {
                'ParameterKey': 'IndexerSGName',
                'ParameterValue': indexer_sg_name
            },
            {
                'ParameterKey': 'DeploymentServerSGName',
                'ParameterValue': deployment_server_sg_name
            },
            {
                'ParameterKey': 'MasterClusterNodeSGName',
                'ParameterValue': master_cluster_node_sg_name
            },
            {
                'ParameterKey': 'LicenseServerSGName',
                'ParameterValue': license_server_sg_name
            },
            {
                'ParameterKey': 'AWSServicesSGName',
                'ParameterValue': aws_services_sg_name
            },
            {
                'ParameterKey': 'CIDRBlock1',
                'ParameterValue': private_subnets_cidrs[0]
            },
            {
                'ParameterKey': 'CIDRBlock2',
                'ParameterValue': private_subnets_cidrs[1]
            },
            {
                'ParameterKey': 'CIDRBlock3',
                'ParameterValue': private_subnets_cidrs[2]
            },
            {
                'ParameterKey': 'ProvisionJumphostSgGroup',
                'ParameterValue': str(provision_jumphost_sg_group).lower()
            },
        ],
        Capabilities=['CAPABILITY_IAM']
    )

    l.debug("Response from cloudformation:")
    l.debug(response)
    l.debug("")

    # Wait until the stack is created
    stack_outputs = wait_until_stack_is_created_and_get_outputs(stack_name, delete_if_failed=True)

    sg_role_to_id['application_load_balancer_sg_id'] = stack_outputs['ApplicationLoadBalancerSGID']
    sg_role_to_id['search_head_sg_id'] = stack_outputs['SearchHeadSGID']
    sg_role_to_id['heavy_forwarder_sg_id'] = stack_outputs['HeavyForwarderSGID']
    sg_role_to_id['deploy_sg_id'] = stack_outputs['DeploySGID']
    sg_role_to_id['indexer_sg_id'] = stack_outputs['IndexerSGID']
    sg_role_to_id['deployment_server_sg_id'] = stack_outputs['DeploymentServerSGID']
    sg_role_to_id['master_cluster_node_sg_id'] = stack_outputs['MasterClusterNodeSGID']
    sg_role_to_id['license_server_sg_id'] = stack_outputs['LicenseServerSGID']
    sg_role_to_id['aws_services_sg_id'] = stack_outputs['AWSServicesSGID']
    jumphost_sg_id = stack_outputs.get('JumphostSGID', None)

    configure_inbound_and_outbound_rules(
        vpc_id=vpc_id,
        sg_role_to_id = sg_role_to_id,
        access_to_load_balancer_sg_id = access_to_load_balancer_sg_id,
        jumphost_sg_id = jumphost_sg_id,
        l=l)


    return sg_role_to_id