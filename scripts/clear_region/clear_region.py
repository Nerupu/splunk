import boto3
from pprint import pprint
import concurrent.futures
import boto3
import argparse
from time import sleep

parser = argparse.ArgumentParser(description='Clear region in AWS')
parser.add_argument('--region', default='us-east-1', help='AWS region to clear architecture in')
parser.add_argument('--dryrun', action='store_true', help='Dry run, no architecture will be deleted, only displayed')
args = parser.parse_args()


def get_sg_id(name):
    security_group_id = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [name]}])['SecurityGroups'][0]['GroupId']
    return security_group_id

def get_sg_ids(security_group_names):
    sg_ids = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_subnet = {executor.submit(get_sg_id, name): name for name in security_group_names}
        for future in concurrent.futures.as_completed(future_to_subnet):
            sg_name = future_to_subnet[future]
            try:
                data = future.result()
            except Exception as exc:
                print(f"Error getting id for sg {sg_name}: {exc}")
            else:
                sg_ids.append(data)
    return sg_ids

def revoke_ingress(sg_id):
    ip_permissions = ec2.describe_security_groups(GroupIds=[sg_id])['SecurityGroups'][0]['IpPermissions']
    if ip_permissions:
        ec2.revoke_security_group_ingress(GroupId=sg_id, IpPermissions=ip_permissions)

def revoke_egress(sg_id):
    ip_permissions_egress = ec2.describe_security_groups(GroupIds=[sg_id])['SecurityGroups'][0]['IpPermissionsEgress']
    if ip_permissions_egress:
        ec2.revoke_security_group_egress(GroupId=sg_id, IpPermissions=ip_permissions_egress)

def delete_all_stacks(region):
    cf_client = boto3.client('cloudformation', region_name=region)
    paginator = cf_client.get_paginator('list_stacks')
    response_iterator = paginator.paginate(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE'])

    print("Listing all stacks in the region:")
    for page in response_iterator:
        stack_summaries = page['StackSummaries']
        for stack_summary in stack_summaries:
            stack_name = stack_summary['StackName']
            print(stack_name)

    confirmation = input(f"\nAre you sure you want to delete all stacks in {region}? (y/n): ")
    if confirmation.lower() == 'y':
        for page in response_iterator:
            stack_summaries = page['StackSummaries']
            for stack_summary in stack_summaries:
                stack_name = stack_summary['StackName']
                print(f"\nDeleting stack: {stack_name}")
                cf_client.delete_stack(StackName=stack_name)
        print("\nStack deletion completed.")
    else:
        print("Aborted")

def get_all_stacks(region):
    cf_client = boto3.client('cloudformation', region_name=region)
    paginator = cf_client.get_paginator('list_stacks')
    response_iterator = paginator.paginate(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE'])
    stacks = []
    for page in response_iterator:
        stack_summaries = page['StackSummaries']
        for stack_summary in stack_summaries:
            stack_name = stack_summary['StackName']
            stacks.append(stack_name)
    return stacks

def get_all_load_balancers(region):
    elb_client = boto3.client('elbv2', region_name=region)
    response = elb_client.describe_load_balancers()
    load_balancers = response['LoadBalancers']
    lb_arns = [lb['LoadBalancerArn'] for lb in load_balancers]
    lb_names = [lb['LoadBalancerName'] for lb in load_balancers]
    return lb_arns, lb_names

import concurrent.futures
import boto3

def get_instance_name_given_instance_id(region, instance_id):
    ec2_client = boto3.client('ec2', region_name=region)
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    try:
        tags = response['Reservations'][0]['Instances'][0]['Tags']
        #search for tag with key Name
        for tag in tags:
            if tag['Key'] == 'Name':
                instance_name = tag['Value']
    except:
        instance_name = instance_id

    

    return instance_id, instance_name

def get_all_instances(region):
    ec2_client = boto3.client('ec2', region_name=region)
    response = ec2_client.describe_instances()
    instances = response['Reservations']
    #filter out instances that are not already terminated
    instances = [instance for instance in instances if instance['Instances'][0]['State']['Name'] != 'terminated']
    #get instance id from instances
    instance_ids = [instance['Instances'][0]['InstanceId'] for instance in instances]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create a thread for each instance ID
        futures = [executor.submit(get_instance_name_given_instance_id, region, instance_id) for instance_id in instance_ids]
        
        # Wait for all threads to complete
        concurrent.futures.wait(futures)

        # Get the result of each thread
        instance_ids_and_names = [future.result() for future in futures]

    return instance_ids_and_names

def revoke_sg_rules(sg_ids):
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_subnet = {executor.submit(revoke_ingress, sg_id): sg_id for sg_id in sg_ids}
        for future in concurrent.futures.as_completed(future_to_subnet):
            sg_id = future_to_subnet[future]
            try:
                data = future.result()
            except Exception as exc:
                print(f"Error revoking ingress for sg {sg_id}: {exc}")
            else:
                print(f"Revoked ingress for sg {sg_id}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_subnet = {executor.submit(revoke_egress, sg_id): sg_id for sg_id in sg_ids}
        for future in concurrent.futures.as_completed(future_to_subnet):
            sg_id = future_to_subnet[future]
            try:
                data = future.result()
            except Exception as exc:
                print(f"Error revoking egress for sg {sg_id}: {exc}")
            else:
                print(f"Revoked egress for sg {sg_id}")

def delete_load_balancers(lb_arns, lb_names):
    elb_client = boto3.client('elbv2', region_name=region)
    for lb_arn, lb_name in zip(lb_arns, lb_names):
        print(f"Deleting load balancer: {lb_name}")
        elb_client.delete_load_balancer(LoadBalancerArn=lb_arn)

def delete_instances(instance_ids_and_names):
    ec2_client = boto3.client('ec2', region_name=region)
    for instance_id, instance_name in instance_ids_and_names:
        print(f"Terminating instance: {instance_name}")
        ec2_client.terminate_instances(InstanceIds=[instance_id])

def delete_stacks(stacks):
    cf_client = boto3.client('cloudformation', region_name=region)
    for stack in stacks:
        print(f"Deleting stack: {stack}")
        cf_client.delete_stack(StackName=stack)

def sleep_info(sleep_time):
    print(f"Sleeping for {sleep_time} seconds...")
    sleep(sleep_time)


if __name__ == '__main__':
    region = args.region
    ec2 = boto3.client('ec2', region_name=region)
    sts = boto3.client('sts', region_name=region)


    account_id = sts.get_caller_identity()['Account']
    print("="*200)
    print(f"Region: {ec2.meta.region_name}")
    print(f"Account ID: {account_id}")
    print("="*200)

    security_group_names = 'EAF-DEPLOY-SG,EAF-LICENSE-SERVER-SG,EAF-HEAVY-FORWARDER-SG,EAF-APPLICATION-LOAD-BALANCER-SG,EAF-DEPLOYMENT-SERVER-SG,EAF-SEARCH-HEAD-SG,EAF-MASTER-CLUSTER-NODE-SG,EAF-INDEXER-SG'.split(',')
    print("Getting security group ids...")
    sg_ids = get_sg_ids(security_group_names)
    print("Getting stack names...")
    stacks = get_all_stacks(region)
    print("Getting load balancers...")
    lb_arns, lb_names = get_all_load_balancers(region)
    print("Getting instances...")
    instance_ids = get_all_instances(region)
    instances_to_be_deleted = []
    all_other_instances = []
    for instance_id, instance_name in instance_ids:
        if 'waa-eaf' in instance_name:
            instances_to_be_deleted.append((instance_id, instance_name))
        else:
            all_other_instances.append((instance_id, instance_name))

    stacks_to_be_deleted = []
    all_other_stacks = []
    for stack in stacks:
        if 'EAF-' in stack:
            stacks_to_be_deleted.append(stack)
        else:
            all_other_stacks.append(stack)


    print(f"Found {len(sg_ids)} security groups to clear")
    print()
    print(f"Security groups to clear (static list):")
    pprint(security_group_names)
    print()
    print(f"Security groups ids to clear:")
    pprint(sg_ids)
    print()
    print("="*200)
    print(f"Stacks to delete in {region}:")
    pprint(stacks_to_be_deleted)
    print("Other stacks:")
    pprint(all_other_stacks)
    print()
    print("="*200)
    print(f"Load balancers to delete in {region}:")
    pprint([f"name: {name}, arn: {arn}" for arn, name in zip(lb_arns, lb_names)])
    print()
    print("="*200)
    print(f"Instances to delete in {region}:")
    pprint(instances_to_be_deleted)
    print()
    print("Other instances:")
    pprint(all_other_instances)
    print("="*200)




    if args.dryrun:
        print("Dry run, no architecture will be deleted")
        exit()

    print("Revoking security group rules...")
    revoke_sg_rules(sg_ids)

    print("Deleting load balancers...")
    delete_load_balancers(lb_arns, lb_names)

    print("Deleting instances...")
    delete_instances(instances_to_be_deleted)
    # sleep_info(60)

    print("Deleting stacks...")
    delete_stacks(stacks)

    print("Done")