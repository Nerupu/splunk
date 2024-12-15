import boto3, logging, json
from utils import validate_template, wait_until_stack_is_created_and_get_outputs
from sg_utils import check_if_sg_with_ports_exists

def create_endpoints(
        vpc_id: str, 
        subnets: list, 
        stack_name: str,
        security_group_id: str,
        route_table_id: str,
        l: logging.Logger = logging.getLogger(__name__)):

    l.info("Checking if three subnets are provided...")
    if len(subnets) != 3:
        l.error("Three subnets must be provided.")
        raise Exception("Three subnets must be provided.")
    l.info("Three subnets provided.")
    l.info("")

    l.info("Checking if VPC endpoints already exist...")
    l.info("")
    ssm_endpoint_exists, ssm_messages_endpoint_exists, s3_endpoint_exists = check_vpc_endpoints_exists(vpc_id, l)

    l.info("SSM endpoint already exists and will not be created.") if ssm_endpoint_exists else l.info("SSM endpoint does not exist and will be created.")
    l.info("SSM Messages endpoint already exists and will not be created.") if ssm_messages_endpoint_exists else l.info("SSM Messages endpoint does not exist and will be created.")
    l.info("S3 endpoint already exists and will not be created.") if s3_endpoint_exists else l.info("S3 endpoint does not exist and will be created.")
    l.info("")

    l.info("Creating endpoints to ssm, ssmmessages, s3...")

    cloudformation_client = boto3.client('cloudformation')
    template_body = validate_template('cf_endpoints.yaml')



    if any(
        [
        not ssm_endpoint_exists,
        not ssm_messages_endpoint_exists,
        not s3_endpoint_exists
        ]
    ):
        l.info("+"*100)
        l.info("Creating stack with following parameters:")
        l.info("")
        l.info(f"Stack name: {stack_name}")
        l.info(f"VPC ID: {vpc_id}")
        l.info(f"Subnet IDs: {subnets}")
        l.info("+"*100)

        response = cloudformation_client.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=[
                {
                    'ParameterKey': 'VpcId',
                    'ParameterValue': vpc_id
                },
                {
                    'ParameterKey': 'SubnetId1',
                    'ParameterValue': subnets[0]
                },
                {
                    'ParameterKey': 'SubnetId2',
                    'ParameterValue': subnets[1]
                },
                {
                    'ParameterKey': 'SubnetId3',
                    'ParameterValue': subnets[2]
                },
                {
                    'ParameterKey': 'CreateSsmEndpoint',
                    'ParameterValue': 'True' if not ssm_endpoint_exists else 'False'
                },
                {
                    'ParameterKey': 'CreateSsmMessagesEndpoint',
                    'ParameterValue': 'True' if not ssm_messages_endpoint_exists else 'False'
                },
                {
                    'ParameterKey': 'CreateS3Endpoint',
                    'ParameterValue': 'True' if not s3_endpoint_exists else 'False'
                },
                {
                    'ParameterKey': 'RouteTableId',
                    'ParameterValue': route_table_id
                },
                {
                    'ParameterKey': 'SecurityGroupId',
                    'ParameterValue': security_group_id
                }
            ],
            Capabilities=[
                'CAPABILITY_IAM',
            ],
        )

        l.debug("Response from create_stack:")
        l.debug("")
        l.debug(response)
        l.debug("")

        l.info("Waiting for stack to be created...")
        stack_outputs = wait_until_stack_is_created_and_get_outputs(stack_name, cloudformation_client)
        l.info("Stack created.")
        l.info("")
        if stack_outputs:
            l.info("Stack outputs:")
            l.info("")
            l.info(json.dumps(stack_outputs, indent=4))
            l.info("")
        l.info("+"*100)

    else:
        l.info("No endpoints were created.")
        l.info("")
        l.info("+"*100)

    return
        



def check_vpc_endpoints_exists(vpc_id, l: logging.Logger = logging.getLogger(__name__)):
    ec2 = boto3.client('ec2')
    response = ec2.describe_vpc_endpoints(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])

    ssm_endpoint_exists = False
    ssm_messages_endpoint_exists = False
    s3_endpoint_exists = False

    for endpoint in response['VpcEndpoints']:
        service_name = endpoint['ServiceName']

        if f"com.amazonaws.{boto3.Session().region_name}.ssm" in service_name:
            l.info(f"SSM Endpoint exists: {endpoint['VpcEndpointId']}")
            ssm_endpoint_exists = True

        if f"com.amazonaws.{boto3.Session().region_name}.ssmmessages" in service_name:
            l.info(f"SSM Messages Endpoint exists: {endpoint['VpcEndpointId']}")
            ssm_messages_endpoint_exists = True

        if f"com.amazonaws.{boto3.Session().region_name}.s3" in service_name:
            l.info(f"S3 Endpoint exists: {endpoint['VpcEndpointId']}")
            s3_endpoint_exists = True

    return ssm_endpoint_exists, ssm_messages_endpoint_exists, s3_endpoint_exists

