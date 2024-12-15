import logging, boto3
from pprint import pprint
import concurrent.futures
from utils import validate_template, wait_until_stack_is_created_and_get_outputs

def create_vpc_if_needed(
        vpc_id:str, 
        args, 
        stack_name:str = 'EAF_VPC', 
        cloudformation_template:str = 'cf_vpc.yaml',
        l:logging.Logger = logging.getLogger(__name__)):
    
    aws_region = boto3.session.Session().region_name
    # Create the VPC if needed
    if vpc_id == "create":
        #create vpc using cloudformation
        l.info("VPC Id has been passed as \'create\'. Creating VPC...")
        l.info("")
        cloudformation_client = boto3.client('cloudformation')

        template_body = validate_template(cloudformation_template)
        
        l.info("+"*100)
        l.info("Creating stack with following parameters:")
        l.info("")
        l.info(f"Stack name: {stack_name}")
        l.info(f"Name prefix: {args.name_prefix}")
        l.info(f"VPC CIDR: {args.vpc_cidr}")
        l.info(f"Public subnet CIDR: {args.public_subnet_cidr}")
        l.info(f"Private subnet CIDR az1: {args.private_subnet_cidr_az1}")
        l.info(f"Private subnet CIDR az2: {args.private_subnet_cidr_az2}")
        l.info(f"Private subnet CIDR az3: {args.private_subnet_cidr_az3}")

        response = cloudformation_client.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=[
                {
                    'ParameterKey': 'EnvironmentName',
                    'ParameterValue': args.name_prefix
                },
                {
                    'ParameterKey': 'VpcName',
                    'ParameterValue': f"{args.name_prefix}-VPC-Splunk"
                },
                {
                    'ParameterKey': 'VpcCIDR',
                    'ParameterValue': args.vpc_cidr
                },
                {
                    'ParameterKey': 'PublicSubnetCIDR',
                    'ParameterValue': args.public_subnet_cidr
                },
                {
                    'ParameterKey': 'PrivateSubnet1CIDR',
                    'ParameterValue': args.private_subnet_cidr_az1
                },
                {
                    'ParameterKey': 'PrivateSubnet2CIDR',
                    'ParameterValue': args.private_subnet_cidr_az2
                },
                {
                    'ParameterKey': 'PrivateSubnet3CIDR',
                    'ParameterValue': args.private_subnet_cidr_az3
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

    else:
        l.info(f"Using existing VPC {vpc_id}")
        l.info(f"Checking if VPC {vpc_id} can be used.")
        # raise Exception("Not implemented yet, need to implement checking if 3 private subnets in different az exists and one public subnet exists in the VPC. ")
        ret = boto3.client('ec2').describe_vpcs(VpcIds=[vpc_id])
        if len(ret['Vpcs']) == 0:
            l.error(f"VPC {vpc_id} does not exist in region {aws_region}")
            exit(1)
        else:
            l.info("VPC exists")
            l.debug("VPC details:")
            l.debug("")
            pprint(ret) if l.level == logging.DEBUG else None
            l.info("")
            l.info("Will use first avaiable public and private subnet in the VPC.")
            l.info("")
            l.info("Getting public and private subnets...")
            l.info("")
            ret = boto3.client('ec2').describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
            l.debug("Subnets details:")
            l.debug("")
            pprint(ret) if l.level == logging.DEBUG else None
            l.info("")
            public_subnet = None
            private_subnets = []
            for subnet in ret['Subnets']:
                if subnet['MapPublicIpOnLaunch'] == True:
                    public_subnet = subnet['SubnetId']
                else:
                    private_subnets.append(subnet['SubnetId'])
            if len(private_subnets) != 3:
                l.error(f"VPC {vpc_id} does not have 3 private subnets in different AZs")
                exit(1)
            l.info(f"Public subnet: {public_subnet}")
            l.info(f"Private subnets: {private_subnets}")
            l.info("")

            l.info("Getting private route table...")
            private_route_table = get_private_route_table(vpc_id)
            if private_route_table is None:
                l.error(f"VPC {vpc_id} does not have private route table")
                exit(1)
            l.info(f"Private route table: {private_route_table}")

            return vpc_id, public_subnet, private_subnets, private_route_table
        
    # Wait until the stack is created
    stack_outputs = wait_until_stack_is_created_and_get_outputs(stack_name)

    # Get the VPC id from the stack outputs
    vpc_id = stack_outputs['VPC']
    public_subnet = stack_outputs['PublicSubnet']
    private_subnet_az1 = stack_outputs['PrivateSubnet1']
    private_subnet_az2 = stack_outputs['PrivateSubnet2']
    private_subnet_az3 = stack_outputs['PrivateSubnet3']
    private_route_table = stack_outputs['PrivateRouteTable']

    return vpc_id, public_subnet, [private_subnet_az1, private_subnet_az2, private_subnet_az3], private_route_table

def vpc_exists(vpc_id):
    ec2 = boto3.client('ec2')

    try:
        response = ec2.describe_vpcs(VpcIds=[vpc_id])
        if response and response['Vpcs']:
            return True
    except boto3.exceptions.botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidVpcID.NotFound':
            return False
        else:
            raise e

    return False

def get_subnet_az(subnet_id):
    ec2 = boto3.resource('ec2')
    subnet = ec2.Subnet(subnet_id)
    return subnet.availability_zone

def wrapper(subnet_id):
    return subnet_id, get_subnet_az(subnet_id)

def get_all_subnets_azs(subnets):
    mapping = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(wrapper, subnet_id) for subnet_id in subnets]
        for future in concurrent.futures.as_completed(futures):
            subnet_id, az = future.result()
            mapping[subnet_id] = az
    return mapping



def get_private_route_table(vpc_id):
    """
    Returns the private route table ID for a given VPC ID.
    """
    # Create a Boto3 EC2 client
    ec2 = boto3.client('ec2')
    
    # Use the client to describe the VPC's route tables
    response = ec2.describe_route_tables(Filters=[
        {'Name': 'vpc-id', 'Values': [vpc_id]},
        {'Name': 'association.main', 'Values': ['false']},
        {'Name': 'route.destination-cidr-block', 'Values': ['0.0.0.0/0']},
    ])
    
    # Look for the private route table in the response
    for route_table in response['RouteTables']:
        for association in route_table['Associations']:
            if association['Main'] == False:
                return route_table['RouteTableId']
    
    # If no private route table was found, return None
    return None
