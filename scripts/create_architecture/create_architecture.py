from cloudformation import *
from stack_utils import *
from security_groups import manage_security_groups
import os
import argparse
from logging_config import logger as l
from dictionary_utils import *
from collections import defaultdict

parser = argparse.ArgumentParser()
parser.add_argument("--config-path", type=str, default="C:\My Project work\POCs\linux Patching\windows_precheck\learning\keys\SRE_TEAM\prasad\vault_automation\EAF\EAF-Splunk-WIP\scripts\json_configurations\default_splunk_configuration.json")

args = parser.parse_args()
config_path = args.config_path
#input_file_path = r'C:\My Project work\POCs\linux Patching\windows_precheck\learning\keys\SRE_TEAM\prasad\vault_automation\EAF\EAF-Splunk-WIP\scripts\json_configurations\default_splunk_configuration.json'


general_parameters, common_instance_parameters, specifications_per_worker = get_architecture_parameters(config_path)

aws_region = general_parameters["aws_region"]
os.environ["AWS_DEFAULT_REGION"] = aws_region
l.info(f"Region = {aws_region}")

account_id = general_parameters["account_id"]

env_name = general_parameters['infrastructure_name_prefix']
vpc_cidr = general_parameters["vpc"].get("cidr", '')
ipam_pool_id = general_parameters["vpc"].get("ipam_pool_id", '')
private_subnets_cidrs = list(filter(None,[
    general_parameters["vpc"].get(f"private_subnet_cidr_az{i}", '') for i in range(1, 100)
]))
private_subnets_cidrs_tier2 = list(filter(None,[
    general_parameters["vpc"].get(f"private_subnet_cidr_az{i}_tier2", '') for i in range(1, 100)
]))
public_subnet_cidr = general_parameters['vpc'].get('public_subnet_cidr', '')

kms_key_alias_name = general_parameters["kms_key_alias"]

instance_profile_data:dict = general_parameters.get("instance_profile", {})
if not instance_profile_data: raise Exception("Instance profile is not defined in config.json")
instance_profile_name = instance_profile_data.get("name", '')
instance_profile_role_name = instance_profile_data.get("role_name", '')
instance_profile_policy_name = instance_profile_data.get("policy_name", '')


if __name__ == "__main__":
    check_if_aws_is_configured(account_id)

    instances_quantity = int(general_parameters.get('instances_quantity', 0))

    if instances_quantity != len(specifications_per_worker):
        raise Exception(f"instances_quantity must be equal to the number of specifications_per_worker. Currently you defined {instances_quantity} instances but provided {len(specifications_per_worker)}. You have to define specifications for each instance, but you can provide empty dicttionary for some of them. Read the documentation for more details.")


    architecture_template = CloudFormationTemplate()

    vpc_id = general_parameters['vpc'].get('id', '')
    if vpc_id == 'create':
        vpc = Resource("VPC", "AWS::EC2::VPC")
        vpc.add_property("CidrBlock", vpc_cidr)
        vpc.add_property("EnableDnsSupport", True)
        vpc.add_property("EnableDnsHostnames", True)
        # vpc.add_property("Tags", [{"Key": "Name", "Value": "VPC-1"}])
        vpc.add_tag("Name", f"{env_name}-VPC")
        architecture_template.add_resource(vpc)
    else:
        vpc = CreatedResource(vpc_id)

    internet_gateway = Resource("InternetGateway", "AWS::EC2::InternetGateway")
    internet_gateway.add_tag("Name", f"{env_name}-IGW")
    architecture_template.add_resource(internet_gateway)

    internet_gateway_attachment = Resource("InternetGatewayAttachment", "AWS::EC2::VPCGatewayAttachment")
    internet_gateway_attachment.add_property("InternetGatewayId", internet_gateway.reference_this_resource())
    internet_gateway_attachment.add_property("VpcId", vpc.reference_this_resource())
    architecture_template.add_resource(internet_gateway_attachment)

    number_of_az = min(3, len(private_subnets_cidrs))
    number_of_subnets = len(private_subnets_cidrs)
    private_subnets:list[Resource] = create_subnets(
        number_of_subnets = number_of_subnets,
        number_of_az = number_of_az,
        cidrs = private_subnets_cidrs,
        vpc = vpc,
        public = False,
        env_name = env_name)
    
    number_of_az = min(3, len(private_subnets_cidrs_tier2))
    number_of_subnets = len(private_subnets_cidrs_tier2)
    private_subnets_tier2:list[Resource] = create_subnets(
        number_of_subnets = number_of_subnets,
        number_of_az = number_of_az,
        cidrs = private_subnets_cidrs_tier2,
        vpc = vpc,
        public = False,
        env_name = env_name,
        tier2 = True)
    

    for subnet in private_subnets+private_subnets_tier2:
        architecture_template.add_resource(subnet)

    public_subnet = Resource(f"PublicSubnet", "AWS::EC2::Subnet")
    public_subnet.add_property("VpcId", vpc.reference_this_resource())
    public_subnet.add_property("CidrBlock", public_subnet_cidr)
    public_subnet.add_property("AvailabilityZone", f"!Select [0, !GetAZs '']")
    public_subnet.add_property("MapPublicIpOnLaunch", True)
    public_subnet.add_tag("Name", f"{env_name} Public Subnet")
    architecture_template.add_resource(public_subnet)

    database_subnet_group = Resource("DatabaseSubnetGroup", "AWS::RDS::DBSubnetGroup")
    database_subnet_group.add_property("DBSubnetGroupDescription", f"{env_name}-Database-Subnet-Group")
    database_subnet_group.add_property("SubnetIds", [subnet.reference_this_resource() for subnet in private_subnets[:2]])
    database_subnet_group.add_tag("Name", f"{env_name}-Database-Subnet-Group")
    architecture_template.add_resource(database_subnet_group)

    nat_gateway_eip = Resource("NatGatewayEIP", "AWS::EC2::EIP")
    nat_gateway_eip.add_dependency(internet_gateway_attachment.logical_id)
    nat_gateway_eip.add_property("Domain", "vpc")
    architecture_template.add_resource(nat_gateway_eip)

    nat_gateway = Resource("NatGateway", "AWS::EC2::NatGateway")
    nat_gateway.add_property("AllocationId", f"!GetAtt {nat_gateway_eip.logical_id}.AllocationId")
    nat_gateway.add_property("SubnetId", public_subnet.reference_this_resource())
    architecture_template.add_resource(nat_gateway)

    public_route_table = Resource("PublicRouteTable", "AWS::EC2::RouteTable")
    public_route_table.add_property("VpcId", vpc.reference_this_resource())
    public_route_table.add_tag("Name", f"{env_name}-Public-RouteTable")
    architecture_template.add_resource(public_route_table)

    public_route = Resource("PublicRoute", "AWS::EC2::Route")
    public_route.add_property("RouteTableId", public_route_table.reference_this_resource())
    public_route.add_property("DestinationCidrBlock", "0.0.0.0/0")
    public_route.add_property("GatewayId", internet_gateway.reference_this_resource())
    architecture_template.add_resource(public_route)

    public_route_table_association = Resource("PublicRouteTableAssociation", "AWS::EC2::SubnetRouteTableAssociation")
    public_route_table_association.add_property("SubnetId", public_subnet.reference_this_resource())
    public_route_table_association.add_property("RouteTableId", public_route_table.reference_this_resource())
    architecture_template.add_resource(public_route_table_association)

    private_route_table = Resource("PrivateRouteTable", "AWS::EC2::RouteTable")
    private_route_table.add_property("VpcId", vpc.reference_this_resource())
    private_route_table.add_tag("Name", f"{env_name}-Private-RouteTable")
    architecture_template.add_resource(private_route_table)

    private_route = Resource("PrivateRoute", "AWS::EC2::Route")
    private_route.add_property("RouteTableId", private_route_table.reference_this_resource())
    private_route.add_property("DestinationCidrBlock", "0.0.0.0/0")
    private_route.add_property("NatGatewayId", nat_gateway.reference_this_resource())
    architecture_template.add_resource(private_route)

    for i in range(len(private_subnets)):
        subnet_route_table_association = Resource(f"SubnetRouteTableAssociation{i}", "AWS::EC2::SubnetRouteTableAssociation")
        subnet_route_table_association.add_property("SubnetId", private_subnets[i].reference_this_resource())
        subnet_route_table_association.add_property("RouteTableId", private_route_table.reference_this_resource())
        architecture_template.add_resource(subnet_route_table_association)
        
    for i in range(len(private_subnets_tier2)):
        subnet_route_table_association = Resource(f"SubnetRouteTableAssociation{i}Tier2", "AWS::EC2::SubnetRouteTableAssociation")
        subnet_route_table_association.add_property("SubnetId", private_subnets_tier2[i].reference_this_resource())
        subnet_route_table_association.add_property("RouteTableId", private_route_table.reference_this_resource())
        architecture_template.add_resource(subnet_route_table_association)


    kms_key = Resource("KMSKey", "AWS::KMS::Key")
    kms_key.add_property("Description", "KMS key for encryption")
    kms_key.add_property("KeyPolicy", {
        "Version": "2012-10-17",
        "Id": "EAF_kms_key_policy",
        "Statement": [{
            "Sid": "Allow administration of the key",
            "Effect": "Allow",
            "Principal": {
                "AWS": f"arn:aws:iam::{account_id}:root"
            },
            "Action": [
                "kms:*"
            ],
            "Resource": "*"
        }]
    })

    kms_key_alias = Resource("KMSKeyAlias", "AWS::KMS::Alias")
    kms_key_alias.add_property("AliasName", f"alias/{kms_key_alias_name}")
    kms_key_alias.add_property("TargetKeyId", kms_key.reference_this_resource())

    l.info(f"Checking if KMS key {kms_key_alias_name} exists...")
    if not check_if_ksm_key_already_exists(kms_key_alias_name):
        architecture_template.add_resource(kms_key)
        architecture_template.add_resource(kms_key_alias)
    else:
        l.info(f"KMS key {kms_key_alias_name} already exists. Retrieving key id...")
        kms_key_id = get_kms_key_id(kms_key_alias_name)
        l.info(f"KMS key id: {kms_key_id}")


    ### SSMINSTANCEPROFILE ###



    ssm_role = Resource("SSMRole", "AWS::IAM::Role")
    ssm_role.add_property("RoleName", instance_profile_role_name)
    ssm_role.add_property("AssumeRolePolicyDocument", {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    })
    ssm_role.add_property("ManagedPolicyArns", ["arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"])

    ansible_policy = Resource("AnsiblePolicy", "AWS::IAM::Policy")
    ansible_policy.add_property("PolicyName", instance_profile_policy_name)
    ansible_policy.add_property("PolicyDocument", {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:AbortMultipartUpload",
                "s3:ListBucket",
                "s3:DeleteObject",
                "s3:GetObjectVersion",
                "s3:ListMultiRegionAccessPoints"
            ],
            "Resource": "*"
        }]
    })
    ansible_policy.add_property("Roles", [ssm_role.reference_this_resource()])

    instance_profile = Resource("InstanceProfile", "AWS::IAM::InstanceProfile")
    instance_profile.add_property("Roles", [ssm_role.reference_this_resource()])
    instance_profile.add_property("InstanceProfileName", instance_profile_name)

    l.info(f"Checking if role {instance_profile_name} exists...")
    instance_profile_name_arn = role_exists(instance_profile_name)
    if instance_profile_name_arn is None:
        architecture_template.add_resource(ssm_role)
        architecture_template.add_resource(ansible_policy)
        architecture_template.add_resource(instance_profile)


    # architecture_template.add_output("RoleArn", ssm_role.get_attribute("Arn"))
    # architecture_template.add_output("RoleName", role_name)
    # architecture_template.add_output("PolicyName", policy_name)
    # architecture_template.add_output("InstanceProfileName", instance_profile_name)

    ### SECURITY GROUPS ###

    sg_resources, sg_rules_resources, all_security_groups = manage_security_groups('security_groups_rules.csv', vpc)



    for sg in sg_resources:
        architecture_template.add_resource(sg)

    for sg_rule in sg_rules_resources:
        for sg in sg_resources:
            sg_rule.add_dependency(sg.logical_id)
        architecture_template.add_resource(sg_rule)


    # SG for endpoints and other AWS services

    aws_services_security_group = Resource("AwsServicesSecurityGroup", "AWS::EC2::SecurityGroup")
    aws_services_security_group.add_property("VpcId", vpc.reference_this_resource())
    aws_services_security_group.add_property("GroupName", "AWS Services Security Group")
    aws_services_security_group.add_property("GroupDescription", "Security group for AWS services")

    ingress_rules = [{
            "IpProtocol": "tcp",
            "FromPort": 443,
            "ToPort": 443,
            "CidrIp": subnet_cidr
        } for subnet_cidr in private_subnets_cidrs] + \
        [{
            "IpProtocol": "tcp",
            "FromPort": 443,
            "ToPort": 443,
            "CidrIp": subnet_cidr
        } for subnet_cidr in private_subnets_cidrs_tier2]
    

    aws_services_security_group.add_property("SecurityGroupIngress", ingress_rules)
    aws_services_security_group.add_property("SecurityGroupEgress", [])
    architecture_template.add_resource(aws_services_security_group)



    ### ENDPOINTS ###

    subnet_references = [subnet.reference_this_resource() for subnet in private_subnets]

    ssm_vpc_endpoint = Resource("SsmVpcEndpoint", "AWS::EC2::VPCEndpoint")
    ssm_vpc_endpoint.add_property("VpcId", vpc.reference_this_resource())
    ssm_vpc_endpoint.add_property("ServiceName", f"com.amazonaws.{aws_region}.ssm")
    ssm_vpc_endpoint.add_property("VpcEndpointType", "Interface")
    ssm_vpc_endpoint.add_property("SubnetIds", subnet_references)
    ssm_vpc_endpoint.add_property("PrivateDnsEnabled", True)
    ssm_vpc_endpoint.add_property("SecurityGroupIds", [aws_services_security_group.reference_this_resource()])
    architecture_template.add_resource(ssm_vpc_endpoint)

    ssm_messages_vpc_endpoint = Resource("SsmMessagesVpcEndpoint", "AWS::EC2::VPCEndpoint")
    ssm_messages_vpc_endpoint.add_property("VpcId", vpc.reference_this_resource())
    ssm_messages_vpc_endpoint.add_property("ServiceName", f"com.amazonaws.{aws_region}.ssmmessages")
    ssm_messages_vpc_endpoint.add_property("VpcEndpointType", "Interface")
    ssm_messages_vpc_endpoint.add_property("SubnetIds", subnet_references)
    ssm_messages_vpc_endpoint.add_property("PrivateDnsEnabled", True)
    ssm_messages_vpc_endpoint.add_property("SecurityGroupIds", [aws_services_security_group.reference_this_resource()])
    architecture_template.add_resource(ssm_messages_vpc_endpoint)

    s3_vpc_endpoint = Resource("S3VpcEndpoint", "AWS::EC2::VPCEndpoint")
    s3_vpc_endpoint.add_property("VpcId", vpc.reference_this_resource())
    s3_vpc_endpoint.add_property("ServiceName", f"com.amazonaws.{aws_region}.s3")
    s3_vpc_endpoint.add_property("VpcEndpointType", "Gateway")
    s3_vpc_endpoint.add_property("RouteTableIds", [private_route_table.reference_this_resource()])
    architecture_template.add_resource(s3_vpc_endpoint)




    ### S3 BUCKET ###

    bucket_name = generate_bucket_name(
        account_id=account_id,
        environment_prefix=env_name,
        region=aws_region,
        software='splunk',
        )

    s3_bucket = Resource("S3Bucket", "AWS::S3::Bucket")
    s3_bucket.add_property("BucketName", bucket_name)
    s3_bucket.add_property("AccessControl", "Private")
    s3_bucket.add_property("VersioningConfiguration", {"Status": "Suspended"})
    s3_bucket.add_property("LifecycleConfiguration", {"Rules": [{"Status": "Disabled", "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}}]})

    s3_bucket_policy = Resource("S3BucketPolicy", "AWS::S3::BucketPolicy")
    s3_bucket_policy.add_property("Bucket", s3_bucket.reference_this_resource())
    s3_bucket_policy.add_property("PolicyDocument", 
    {
    "Version": "2012-10-17",
    "Statement": [
        {
        "Sid": "AllowVPCPrivateSubnetRead",
        "Effect": "Allow",
        "Principal": "*",
        "Action": ["s3:GetObject", "s3:ListBucket"],
        "Resource": [
            f"!Sub arn:aws:s3:::${{{s3_bucket.logical_id}}}", 
            f"!Sub arn:aws:s3:::${{{s3_bucket.logical_id}}}/*"
            ],
        "Condition": {
            "StringEquals": {
            "aws:SourceVpc": vpc.reference_this_resource()
            }
        }
        }
    ]
    })

    if not check_if_bucket_alerady_exist(bucket_name):
        architecture_template.add_resource(s3_bucket)
        architecture_template.add_resource(s3_bucket_policy)



    ### DUMPING ###

    # dump = dump_template(architecture_template)
    # # exit()
    # deploy_stack(dump)


    ### PREPARE VM PARAMETERS ###


    # pprint(instances_list)

    dump = dump_template(architecture_template)
    # exit()
    stack_name=f'EAF-Architecture-Stack-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
    deploy_stack(dump, stack_name)

    list_of_resources = get_list_of_resources_from_stack(stack_name)
    # list_of_resources = get_list_of_resources_from_stack("EAF-Architecture-Stack-20230612095518")

    def get_resource_from_list(resource_type, list_of_resources):
        for resource in list_of_resources:
            if resource['ResourceType'] == resource_type:
                return resource['PhysicalResourceId']
        return None
    
    def get_subnets_from_list(list_of_resources):
        subnets = []
        subnets_tier2 = []
        for resource in list_of_resources:
            if resource['ResourceType'] == 'AWS::EC2::Subnet' and not resource['LogicalResourceId'].startswith('Public'):
                if 'Tier2' in resource['LogicalResourceId']:
                    subnets_tier2.append(resource['PhysicalResourceId'])
                else:
                    subnets.append(resource['PhysicalResourceId'])
        return subnets, subnets_tier2
    
    def get_security_groups_from_list(list_of_resources):
        security_groups = {}
        for resource in list_of_resources:
            if resource['ResourceType'] == 'AWS::EC2::SecurityGroup':
                security_groups[resource['LogicalResourceId']] = resource['PhysicalResourceId']
        return security_groups

    subnets, subnets_tier2 = get_subnets_from_list(list_of_resources)
    security_groups_logical_to_id = get_security_groups_from_list(list_of_resources)
    db_subnet_group = get_resource_from_list('AWS::RDS::DBSubnetGroup', list_of_resources)
    pprint(security_groups_logical_to_id)

    all_worker_types = list(set(map(lambda x: x['worker_type'], specifications_per_worker)))

    subnet_dispenser = SubnetDispenser(all_worker_types=all_worker_types, subnets=subnets, subnets_tier2 = subnets_tier2)

    instances_list = []
    vm_types_count = defaultdict(int)

    for worker_specification in specifications_per_worker:
        worker_dict = {}
        worker_dict['vm_instance_type'] = get_from_dict_with_check(worker_specification, common_instance_parameters, 'instance_type')
        # worker_dict['vm_ami_name'] = 'ami-0a6006bac3b9bb8d3' #TODO: Create dynamic ami filtr to search for CCP AMI
        worker_dict['vm_ami_name'] = get_from_dict_with_check(worker_specification, common_instance_parameters, 'ami_name')
        worker_dict['vm_instance_profile'] = instance_profile_name


        # worker_dict['vm_sg_list'] = get_from_dict_with_check(worker_specification, common_parameters, 'security_groups')
        # worker_dict['vm_sg_list'] = list(set(worker_dict['vm_sg_list']))
        ## WORKER TYPE
        worker_dict['vm_worker_type'] = get_worker_type(
            worker_specification, 
            common_instance_parameters, 
            supported_types = all_security_groups)


        # WORKER SECURITY GROUPS
        worker_dict['vm_sg_list'] = [security_groups_logical_to_id[worker_dict['vm_worker_type']]]

        ## TAGS
        worker_dict['vm_tags'] = get_tags(worker_specification, common_instance_parameters)

        ## SUBNET
        worker_dict['vm_subnet'] = subnet_dispenser.next(worker_dict['vm_worker_type'])
        
        ## NAME
        # dependant on 'vm_tags', 'vm_worker_type'  from worker_dict
        worker_dict['vm_name'] = create_vm_name(worker_dict, aws_region, vm_types_count)

        ## VOLUMES, root has to be set, data volumes are optional
        worker_dict = manage_volumes(worker_specification, common_instance_parameters, worker_dict)

        ## Data from terraform
        # ami_architecture        = "x86_64"
        # ami_root_device_type    = "ebs"
        # ami_virtualization_type = "hvm"
        # ccp_ami_owner           = "759543830175"

        # worker_dict['vm_ami_architecture'] = ami_architecture
        # worker_dict['vm_ami_root_device_type'] = ami_root_device_type
        # worker_dict['vm_ami_virtualization_type'] = ami_virtualization_type
        # worker_dict['vm_ami_owner'] = ccp_ami_owner
        
        #needed outputs of VMS, type, instance_id, private_dns

        instances_list.append(worker_dict)

    terraform_dict = dict()
    #aws region, account_id, kms_key_id, rds_config, instances_list
    terraform_dict['aws_region'] = general_parameters['aws_region']
    terraform_dict['account_id'] = general_parameters['account_id']
    terraform_dict['kms_key_id'] = get_resource_from_list('AWS::KMS::Key', list_of_resources) if get_resource_from_list('AWS::KMS::Key', list_of_resources) is not None else kms_key_id
    terraform_dict['instances_list'] = instances_list


    #        "load_balancer": {  
        #     "tags" : {
        #         "environment": "dev",
        #         "product": "splunk",
        #         "application": "splunk",
        #         "ccp_managed": "core",
        #         "compliance": "test",
        #         "data_residency": "eea",
        #         "instance": "uk",
        #         "business_unit": "test1"
        #     } 
        # },


    # inputs_dict['load_balancer'] = workflow_config['general_parameters']['load_balancer']
    # inputs_dict['load_balancer']['security_groups'] = [sg_mapping['application_load_balancer_sg_id']]
    # inputs_dict['load_balancer']['names'] = create_lb_names(inputs_dict)
    pprint(security_groups_logical_to_id)
    terraform_dict['load_balancer'] = general_parameters['load_balancer']
    terraform_dict['load_balancer']['security_groups'] = [security_groups_logical_to_id['ApplicationLoadBalancer']]
    terraform_dict['load_balancer']['names'] = create_lb_names(general_parameters)

    pprint(terraform_dict)

    with open('../../terraform/terraform.tfvars.json', "w") as tfvars:
        json.dump(terraform_dict, tfvars, indent=4)
    

    env_file = os.getenv("GITHUB_ENV")
    if env_file is not None:
        with open(env_file, "a+") as env:
            l.info("Current content of github env file")
            l.info(env.read())

            env.write(f"AWS_REGION={general_parameters['aws_region']}\n")
            env.write(f"S3_BUCKET_NAME={bucket_name}\n") # this sloud be final bucket name, but for now it has to be manually crated so name is hardcoded
            #env.write(f"S3_BUCKET_NAME=eaf-splunk-binaries\n")


        with open(env_file, "r") as env:
            l.info("Updated content of github env file")
            l.info(env.read())