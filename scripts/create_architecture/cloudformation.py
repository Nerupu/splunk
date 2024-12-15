import datetime
import boto3
import logging
from pprint import pprint
# import botocore
import json
import io
import re
import os, sys
import yaml
from stack_utils import *
# import ruamel.yaml as yml
from collections import OrderedDict
from logging_config import logger as l

yaml.Dumper.ignore_aliases = lambda self, data: True
yaml.add_representer(OrderedDict, lambda dumper, data: dumper.represent_mapping('tag:yaml.org,2002:map', data.items()))

class Resource:
    def __init__(self, logical_id, resource_type) -> None:
        self.logical_id = logical_id
        self.resource_type = resource_type
        self.properties = OrderedDict()
        self.depends_on = []

    def add_property(self, property_name:str, property_value):
        self.properties[property_name] = property_value

    def add_dependency(self, dependency_logical_id):
        if dependency_logical_id not in self.depends_on:
            self.depends_on.append(dependency_logical_id)

    def add_tag(self, key, value):
        tags = self.properties.get("Tags", [])
        tags.append({"Key": key, "Value": value})
        self.add_property("Tags", tags)
    
    def reference_this_resource(self):
        return f"!Ref {self.logical_id}"

    def dump(self):
        # data = yml.comments.CommentedMap()
        data = OrderedDict()
        data["Type"] = self.resource_type
        data["Properties"] = self.properties
        if self.depends_on:
            data["DependsOn"] = self.depends_on

        return data

class CreatedResource(Resource):
    def __init__(self, resource_id) -> None:
        self.resource_id = resource_id
    
    def reference_this_resource(self):
        return self.resource_id

class CloudFormationTemplate:
    def __init__(self) -> None:
        
        self.aws_template_format_version = "2010-09-09"
        self.description = "AWS CloudFormation Template for the AWS CloudFormation Template"
        # self.resources = yml.comments.CommentedMap()
        self.resources = OrderedDict()
        self.outputs = OrderedDict()
        # self.outputs = yml.comments.CommentedMap()
        self.temaplate_body = None
    
    def add_resource(self, resource: Resource):
        self.resources[resource.logical_id] = resource.dump()

    def add_output(self, output_name, output_value):
        if '!Ref' not in output_value:
            l.info("Output value should be a reference to a resource")
        self.outputs[output_name] = {"Value": output_value}

    def dump(self):
        # data = yml.comments.CommentedMap()
        data = OrderedDict()
        # data = {"AWSTemplateFormatVersion": self.aws_template_format_version, "Description": self.description, "Resources": self.resources, "Outputs": self.outputs}
        data["AWSTemplateFormatVersion"] = self.aws_template_format_version
        data["Description"] = self.description
        data["Resources"] = self.resources
        if self.outputs:
            data["Outputs"] = self.outputs
        dump = io.StringIO()
        yaml.dump(data, dump, default_style=None, default_flow_style=False)
        return dump.getvalue()

def create_subnets(number_of_subnets:int, number_of_az:int, cidrs:list, vpc:Resource, public=False, env_name:str = "EMPTY_ENV_NAME", tier2:bool = False):
    assert number_of_subnets == len(cidrs)
    subnets = []
    for i in range(number_of_subnets):
        subnet_logical_name = f"Subnet{i}" if not tier2 else f"Subnet{i}Tier2"
        subnet = Resource(subnet_logical_name, "AWS::EC2::Subnet")
        subnet.add_property("VpcId", vpc.reference_this_resource())
        subnet.add_property("CidrBlock", cidrs[i])
        subnet.add_property("AvailabilityZone", f"!Select [{i % number_of_az}, !GetAZs '']")
        subnet.add_property("MapPublicIpOnLaunch", public)
        subnet_name_tag = f"{env_name} Subnet{i} AvailabilityZone{i % number_of_az}" if not tier2 else f"{env_name} Subnet{i} AvailabilityZone{i % number_of_az} Tier 2"
        subnet.add_tag("Name", subnet_name_tag)
        subnets.append(subnet)
    return subnets


def get_architecture_parameters(input_file_path:str):

    #check if file exists under given path
    if not os.path.isfile(input_file_path):
        raise Exception(f"File {input_file_path} does not exist. Error while looking for architecture configuration file.")

    with open(input_file_path, "r") as input_file:
        config_content = json.load(input_file)
    general_parameters = config_content.get("general_parameters", None)
    common_instance_parameters = config_content.get("common_instance_parameters", None)
    specifications_per_worker = config_content.get("specifications_per_worker", None)

    if not general_parameters:
        raise Exception("General parameters are missing in the configuration file.")
    
    if not common_instance_parameters:
        l.info("WARNING: Common instance parameters are missing in the configuration file.")

    if not specifications_per_worker:
        raise Exception("Specifications per worker are missing in the configuration file.")

    return general_parameters, common_instance_parameters, specifications_per_worker

def check_if_bucket_alerady_exist(bucket_name:str, l:logging.Logger = logging.getLogger(__name__)):
    s3_client = boto3.client('s3')
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        l.info(f"Bucket with name {bucket_name} already exist.")
        l.info("")
        return True
    except Exception as e:
        l.info(f"Bucket with name {bucket_name} does not exist or you do not have permissions to read it.")
        l.info("")
        return False

def check_if_ksm_key_already_exists(kms_alias_name:str, l:logging.Logger = logging.getLogger(__name__)):
    kms_client = boto3.client('kms')
    try:
        kms_client.describe_key(KeyId=f"alias/{kms_alias_name}")
        l.info(f"KMS key with alias {kms_alias_name} already exist.")
        l.info("")
        return True
    except Exception as e:
        l.info(f"KMS key with alias {kms_alias_name} does not exist or you do not have permissions to read it.")
        l.info("")
        return False

def dump_template(template: CloudFormationTemplate):
    dump = template.dump().replace('!!omap','')
    for i, line in enumerate(dump.splitlines()):
        if '!' in line:
            line = line.replace('\'','')
        dump = dump.replace(dump.splitlines()[i], line)
    dump = dump.replace('!GetAZs ','!GetAZs \'\'')
    l.info("Dumping template to architecture_template.yaml file...")
    with open("architecture_template.yaml", "w") as output_file:
        output_file.write(dump)
    l.info("Validating template...")
    validate_template(dump)
    return dump

def deploy_stack(dump, stack_name):


    l.info(f"Creating stack {stack_name}...")
    cloudformation_client = boto3.client('cloudformation')
    response = cloudformation_client.create_stack(
        StackName=stack_name,
        TemplateBody=dump,
        Capabilities=[
            'CAPABILITY_IAM',
            'CAPABILITY_NAMED_IAM'
        ],
    )

    outputs = wait_until_stack_is_created_and_get_outputs(stack_name)
    pprint(outputs)

def role_exists(role_name):
    iam = boto3.client('iam')

    paginator = iam.get_paginator('list_roles')
    for page in paginator.paginate():
        for role in page['Roles']:
            if role['RoleName'] == role_name:
                return role['Arn']

    return False

def get_kms_key_id(kms_key_alias_name):
    kms_client = boto3.client('kms')
    response = kms_client.describe_key(KeyId=f"alias/{kms_key_alias_name}")
    return response['KeyMetadata']['KeyId']

def validate_bucket_name(bucket_name, l:logging.Logger = logging.getLogger(__name__)):
    name_is_valid = True
    validation_code = None
    # Check if bucket name length is between 3 and 63 characters
    if len(bucket_name) < 3 or len(bucket_name) > 63:
        l.error(f"Bucket name {bucket_name} has less than 3 or more than 63 characters.")
        name_is_valid = False
        validation_code = 1

    # Check if bucket name starts and ends with a lowercase letter or number
    if not re.match('^[a-z0-9].*[a-z0-9]$', bucket_name):
        l.error(f"Bucket name {bucket_name} does not start and end with a lowercase letter or number.")
        name_is_valid = False
        validation_code = 2

    # Check if bucket name contains only lowercase letters, numbers, periods, and hyphens
    if not re.match('^[a-z0-9.-]*$', bucket_name):
        l.error(f"Bucket name {bucket_name} contains characters other than lowercase letters, numbers, periods, and hyphens.")
        name_is_valid = False
        validation_code = 3

    # Check if bucket name contains consecutive periods or hyphens, or period and hyphen together
    if re.search('(\.\.)|(\-\-)|(\.-)|(-\.)', bucket_name):
        l.error(f"Bucket name {bucket_name} contains consecutive periods or hyphens, or period and hyphen together.")
        name_is_valid = False
        validation_code = 4

    # Check if bucket name follows the IPv4-like address pattern
    if re.match('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', bucket_name):
        l.error(f"Bucket name {bucket_name} follows the IPv4-like address pattern.")
        name_is_valid = False
        validation_code = 5

    # Check if bucket name contains uppercase letters
    if re.search('[A-Z]', bucket_name):
        l.error(f"Bucket name {bucket_name} contains uppercase letters.")
        name_is_valid = False
        validation_code = 6

    # Check if bucket name contains underscores
    if re.search('_', bucket_name):
        l.error(f"Bucket name {bucket_name} contains underscores.")
        name_is_valid = False
        validation_code = 7

    # Check if bucket name contains adjacent symbols
    if re.search('[-.]{2,}', bucket_name):
        l.error(f"Bucket name {bucket_name} contains adjacent symbols.")
        name_is_valid = False
        validation_code = 8

    # Check if bucket name has a hyphen next to a period, e.g., "my-.bucket"
    if re.search('\.-|-\.', bucket_name):
        l.error(f"Bucket name {bucket_name} has a hyphen next to a period.")
        name_is_valid = False
        validation_code = 9

    return name_is_valid, validation_code

def generate_bucket_name(
    software:str, 
    environment_prefix:str = 'prod',
    account_id:str = None,
    region:str = None
):

    account_id = boto3.client('sts').get_caller_identity().get('Account') if account_id is None else account_id
    region = boto3.session.Session().region_name if region is None else region

    bucket_name = f"{environment_prefix}-{account_id}-{software}-{region}".lower()

    valid_bucket, validation_code = validate_bucket_name(bucket_name)
    if not valid_bucket:
        l.error(f"Environment prefix: {environment_prefix}")
        l.error(f"Account ID: {account_id}")
        l.error(f"Software: {software}")
        l.error(f"Region: {region}")
        l.error(f"Generated bucket name: {bucket_name}")
        l.error(f"Generated bucket name {bucket_name} is not valid.")
        l.error(f"Validation code: {validation_code}")

        raise Exception(f"Generated bucket name {bucket_name} is not valid.")

    return bucket_name

def get_list_of_resources_from_stack(stack_name):
    cf = boto3.client('cloudformation')
    resp = cf.describe_stack_resources(StackName=stack_name)['StackResources']


    resources_list = []
    for resource in resp:
        resources_list.append({
            'LogicalResourceId': resource['LogicalResourceId'],
            'PhysicalResourceId': resource['PhysicalResourceId'],
            'ResourceType': resource['ResourceType']
        })
    return resources_list