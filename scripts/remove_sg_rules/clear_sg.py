import concurrent.futures
import boto3
import argparse

parser = argparse.ArgumentParser(description='Clear security groups')
parser.add_argument('--dryrun', action='store_true', help='Dry run, no security groups rules will be deleted')
args = parser.parse_args()
# create an EC2 client
ec2 = boto3.client('ec2')

# replace sg_name with your actual security group name
security_group_names = 'EAF-DEPLOY-SG,EAF-LICENSE-SERVER-SG,EAF-HEAVY-FORWARDER-SG,EAF-APPLICATION-LOAD-BALANCER-SG,EAF-DEPLOYMENT-SERVER-SG,EAF-SEARCH-HEAD-SG,EAF-MASTER-CLUSTER-NODE-SG,EAF-INDEXER-SG,'
security_group_names = security_group_names.split(',')
sg_ids = []

def get_sg_id(name):
    security_group_id = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [name]}])['SecurityGroups'][0]['GroupId']
    return security_group_id

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


def revoke_ingress(sg_id):
    ip_permissions = ec2.describe_security_groups(GroupIds=[sg_id])['SecurityGroups'][0]['IpPermissions']
    if ip_permissions:
        ec2.revoke_security_group_ingress(GroupId=sg_id, IpPermissions=ip_permissions)

def revoke_egress(sg_id):
    ip_permissions_egress = ec2.describe_security_groups(GroupIds=[sg_id])['SecurityGroups'][0]['IpPermissionsEgress']
    if ip_permissions_egress:
        ec2.revoke_security_group_egress(GroupId=sg_id, IpPermissions=ip_permissions_egress)

print(f"Found {len(sg_ids)} security groups to clear")
print(f"Security groups to clear: {sg_ids}")

if args.dryrun:
    print("Dry run, no security groups rules will be deleted")
    exit()

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