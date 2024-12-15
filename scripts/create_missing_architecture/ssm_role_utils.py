import boto3, logging
from utils import validate_template, wait_until_stack_is_created_and_get_outputs

def role_exists(role_name):
    iam = boto3.client('iam')

    paginator = iam.get_paginator('list_roles')
    for page in paginator.paginate():
        for role in page['Roles']:
            if role['RoleName'] == role_name:
                return role['Arn']

    return False

def get_instance_profile_name_from_role_arn(role_arn: str):
    iam = boto3.client('iam')

    role_name = role_arn.split("/")[-1]
    response = iam.list_instance_profiles_for_role(
        RoleName=role_name
    )

    if 'InstanceProfiles' in response and len(response['InstanceProfiles']) > 0:
        instance_profile_name = response['InstanceProfiles'][0]['InstanceProfileName']
        return instance_profile_name
    else:
        return None

def create_ssm_role(
        stack_name:str, 
        role_name:str = "SSMRole", 
        policy_name:str = 'AnsiblePolicy', 
        instance_profile_name:str = 'SSMInstanceProfile', 
        l:logging.Logger = logging.getLogger(__name__), 
        delete_if_failed:bool = False):
    
    
    role_arn = role_exists(role_name)
    if role_arn:
        l.info(f"Role {role_name} already exists")
        l.info("Using existing role")
        instance_profile_name = get_instance_profile_name_from_role_arn(role_arn)
        return instance_profile_name
    
    cloudformation_client = boto3.client('cloudformation')

    template_body = validate_template('cf_instance_profile.yaml')

    cloudformation_client = boto3.client('cloudformation')

    response = cloudformation_client.create_stack(
        StackName=stack_name,
        TemplateBody=template_body,
        Parameters=[
            {
                'ParameterKey': 'RoleName',
                'ParameterValue': role_name
            },
            {
                'ParameterKey': 'PolicyName',
                'ParameterValue': policy_name
            },
            {
                'ParameterKey': 'InstanceProfileName',
                'ParameterValue': instance_profile_name
            }

        ],
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
    )

    l.debug("")
    l.debug(response)
    l.debug("")

    # Wait until the stack is created
    stack_outputs = wait_until_stack_is_created_and_get_outputs(stack_name, delete_if_failed=delete_if_failed)

    l.debug("")
    l.debug(stack_outputs)
    l.debug("")

    return stack_outputs['InstanceProfileName']
