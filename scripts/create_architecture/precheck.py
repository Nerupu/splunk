# import boto3
# import json
# accout_id = '131213109016'



# sts_client = boto3.client('sts',region_name ='eu-west-2')
# response= sts_client.assume_role(RoleArn = "arn:aws:sts::131213109016:role/EAF-GITHUB-ROLE-2023-09-26-15-10-3-GitHubTokenRole-2NT6ATUS36SC",RoleSessionName = "GitHubActionSession")
# print("assoumed role:",json.dumps(response,indent=4,default=str))
# creds = response["Credentials"]
# print("creds:",json.dumps(creds,indent=4,default=str))

# def check_if_aws_is_configured(accout_id):
#     sts_client = boto3.client('sts')
#     try:
#         print("Checking if AWS is configured by requesting caller identity...")
#         ret = sts_client.get_caller_identity()
#         print(f"userId:     {ret['UserId']}")
#         print(f"accountId:  {ret['Account']}")
#         print(f"arn:        {ret['Arn']}")
#         print("AWS is configured")
#         print("")

#         if accout_id != ret['Account']:
#             print(f"Account ID mismatch: {accout_id} != {ret['Account']}")
#             exit(1)

#     except Exception as e:
#         print("AWS is not configured")
#         print(e)
#         exit(1)

# print(check_if_aws_is_configured(accout_id))
import boto3
from botocore.exceptions import ClientError




class AWSResourceTagChecker:
    def __init__(self):
        # self.session = boto3.Session(
        #     aws_access_key_id=aws_access_key,
        #     aws_secret_access_key=aws_secret_key,
        # )
        self.ec2_client = boto3.client('ec2')
        self.elbv2_client = boto3.client('elbv2')

    def _check_resource_tag(self, resource_type, tag_key, tag_value):
        if resource_type == 'alb':
            response = self.elbv2_client.describe_load_balancers()
        else:
            response = self.ec2_client.describe_vpcs() if resource_type == 'vpc' else self.ec2_client.describe_subnets()

        for resource in response.get(resource_type.capitalize() + 's', []):
            for tag in resource.get('Tags', []):
                if tag['Key'] == tag_key and tag['Value'] == tag_value:
                    return True
        return False

    def check_instance_tag(self, tag_key, tag_value):
        response = self.ec2_client.describe_instances()
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                for tag in instance.get('Tags', []):
                    if tag['Key'] == tag_key and tag['Value'] == tag_value:
                        return True
        return False

    def check_vpc_tag(self, tag_key, tag_value):
        return self._check_resource_tag('vpc', tag_key, tag_value)

    def check_subnet_tag(self, tag_key, tag_value):
        return self._check_resource_tag('subnet', tag_key, tag_value)

    def check_alb_tag(self, tag_key, tag_value):
        return self._check_resource_tag('alb', tag_key, tag_value)

# Example usage
#access_key, secret_key = get_aws_credentials()
checker = AWSResourceTagChecker()
instance_result = checker.check_instance_tag('product', 'Splunk')
vpc_result = checker.check_vpc_tag('product', 'Splunk')
subnet_result = checker.check_subnet_tag('product', 'Splunk')
alb_result = checker.check_alb_tag('product', 'Splunk')


print(f"EC2 instance with 'Splunk' tag: {instance_result}")
print(f"VPC with 'Splunk' tag: {vpc_result}")
print(f"Subnet with 'Splunk' tag: {subnet_result}")
print(f"ALB with 'Splunk' tag: {alb_result}")
if not instance_result and not vpc_result and not subnet_result and not alb_result:
    print("All functions returned False. Proceeding with the script.")
    # Add your script logic here
else:
    print("At least one function returned True. Exiting the script.")
    exit(1)
