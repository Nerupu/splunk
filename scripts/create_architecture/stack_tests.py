import boto3, os
from pprint import pprint

os.environ['AWS_DEFAULT_REGION'] = 'eu-west-2'

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

list_of_resources = get_list_of_resources_from_stack('architecture-test-stack-20230607152510')

pprint(list(filter(lambda x: x['ResourceType'] == 'AWS::EC2::Instance', list_of_resources)))

instances_list = list(filter(lambda x: x['ResourceType'] == 'AWS::EC2::Instance', list_of_resources))

only_ids = list(map(lambda x: x['PhysicalResourceId'], instances_list))

#start the instances
ec2 = boto3.client('ec2')
ec2.start_instances(InstanceIds=only_ids)

#stop the instances
ec2.stop_instances(InstanceIds=only_ids)
