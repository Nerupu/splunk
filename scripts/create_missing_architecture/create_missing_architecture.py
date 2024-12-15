import os
import datetime
import json
from pprint import pprint
from utils import *
from sg_utils import create_all_security_groups
from vpc_utils import create_vpc_if_needed, get_all_subnets_azs
from ssm_role_utils import create_ssm_role
from endpoints_utils import create_endpoints
from s3_utils import create_s3_bucket


if __name__ == "__main__":
    l = configure_logger(logging.INFO)

    # Here we assume that aws cli is configured which it should be when using this script
    check_if_aws_is_configured()

    args = configure_argparser()
    name_prefix = args.name_prefix
    provision_jumphost_sg_group = True if args.provision_jumphost_sg_group == 'true' else False

    l.setLevel(parse_loglevel(args.loglevel))

    # Set working directory to the directory of the script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))


    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    stack_names = {
        "vpc": f"{name_prefix}-VPC-STACK-{timestamp}",
        "SSMRole": f"{name_prefix}-SSM-ROLE-STACK-{timestamp}",
        "SecurityGroup": f"{name_prefix}-SECURITY-GROUP-STACK-{timestamp}",
        "Endpoints": f"{name_prefix}-ENDPOINTS-STACK-{timestamp}",
        "S3Bucket": f"{name_prefix}-S3-BUCKET-STACK-{timestamp}",
        }
    
    l.info(f"Region used for deployment: {boto3.session.Session().region_name}")
    l.info("")

    l.info("="*100)
    l.info("")


    vpc_id = args.vpc_id
    vpc_id, public_subnet, private_subnets, private_route_table = create_vpc_if_needed(
        vpc_id=vpc_id, 
        stack_name=stack_names['vpc'],
        args=args,
        l=l
        )

    l.info("VPC setup successful")
    l.info("")
    l.info(f"VPC ID: {vpc_id}")
    l.info(f"Public subnet: {public_subnet}")
    l.info(f"Private subnets:")
    mapping = get_all_subnets_azs(private_subnets)
    for subnet in private_subnets:
        l.info(f"\t{subnet}, az: {mapping[subnet]}")
        # l.info(f"\t{subnet}, az: {get_subnet_az(subnet)}")
    l.info("")
        
    l.info("="*100)
    l.info("")

    l.info("Setting up security groups")
    l.info("")

    deafult_sg_names = {
        "aws_services_sg_name": f"{name_prefix}-AWS-SERVICES-SG",
        "application_load_balancer_sg_name": f"{name_prefix}-APPLICATION-LOAD-BALANCER-SG",
        "search_head_sg_name": f"{name_prefix}-SEARCH-HEAD-SG",
        "heavy_forwarder_sg_name": f"{name_prefix}-HEAVY-FORWARDER-SG",
        "deploy_sg_name": f"{name_prefix}-DEPLOY-SG",
        "indexer_sg_name": f"{name_prefix}-INDEXER-SG",
        "deployment_server_sg_name": f"{name_prefix}-DEPLOYMENT-SERVER-SG",
        "master_cluster_node_sg_name": f"{name_prefix}-MASTER-CLUSTER-NODE-SG",
        "license_server_sg_name": f"{name_prefix}-LICENSE-SERVER-SG",
    }



    sg_role_to_id = create_all_security_groups(
        vpc_id=vpc_id,
        stack_name=stack_names['SecurityGroup'],
        access_to_load_balancer_sg_id=args.access_to_load_balancer_sg_id,
        aws_services_sg_name=deafult_sg_names['aws_services_sg_name'],
        application_load_balancer_sg_name=deafult_sg_names['application_load_balancer_sg_name'],
        search_head_sg_name=deafult_sg_names['search_head_sg_name'],
        heavy_forwarder_sg_name=deafult_sg_names['heavy_forwarder_sg_name'],
        deploy_sg_name=deafult_sg_names['deploy_sg_name'],
        indexer_sg_name=deafult_sg_names['indexer_sg_name'],
        deployment_server_sg_name=deafult_sg_names['deployment_server_sg_name'],
        master_cluster_node_sg_name=deafult_sg_names['master_cluster_node_sg_name'],
        license_server_sg_name=deafult_sg_names['license_server_sg_name'],
        private_subnets=private_subnets,
        provision_jumphost_sg_group=provision_jumphost_sg_group,
        l=l
    )

    l.info("Security group setup done")
    l.info("")

    l.info(f"Security Group IDs: ")
    for role, sg_id in sg_role_to_id.items():
        l.info(f"\t{role}: {sg_id}")
    
    l.info("")

    l.info("="*100)
    l.info("")

    l.info("Setting up SSM Role")
    l.info("")

    ssm_instance_profile = create_ssm_role(
        delete_if_failed = not args.keep_stack_if_failed,
        stack_name = stack_names['SSMRole'],
        instance_profile_name=args.ssm_profile_name,
        role_name=args.ssm_role_name,
        policy_name=args.ssm_policy_name,
        l=l
        )

    l.info("SSM Role setup done")
    l.info("")

    l.info(f"SSM Instance Profile Name: {ssm_instance_profile}")
    l.info("")

    l.info("="*100)
    l.info("")

    l.info("Setting up endpoints")
    l.info("")
    
    create_endpoints(
        vpc_id = vpc_id, 
        subnets = private_subnets,
        stack_name = stack_names['Endpoints'],
        security_group_id = sg_role_to_id['aws_services_sg_id'],
        route_table_id = private_route_table,
        l=l
        )

    l.info("Endpoints setup done")
    l.info("")

    l.info("="*100)
    l.info("")

    l.info("Setting up S3 Bucket")
    l.info("")

    s3_bucket_name = create_s3_bucket(
        stack_name=stack_names['S3Bucket'],
        vpc_id=vpc_id,
        l=l
        )
    
    l.info("S3 Bucket setup done")
    l.info("")

    l.info(f"S3 Bucket Name: {s3_bucket_name}")
    l.info("")

    # Write all the outputs to a file
    json_format = {
        "vpc_id": vpc_id,
        "public_subnet": public_subnet,
        "private_subnet_az1": private_subnets[0],
        "private_subnet_az2": private_subnets[1],
        "private_subnet_az3": private_subnets[2],
        "s3_bucket_name": s3_bucket_name,
        "ssm_instance_profile": ssm_instance_profile
    }

    l.info("="*100)
    l.info("")

    l.info("Writing outputs and sg mappings to files")
    l.info("")

    outputs_location = args.outputs_location

    if not os.path.exists(outputs_location):
        os.makedirs(outputs_location)

    outputs_path = f'{outputs_location}/outputs.json'
    with open(outputs_path, 'w') as f:
        json.dump(json_format, f, indent=4)
    l.info(f"Outputs written to {outputs_path}")


    sg_mapping_path = f'{outputs_location}/sg_mapping.json'
    with open(sg_mapping_path, 'w') as f:
        json.dump(sg_role_to_id, f, indent=4)
    l.info(f"Security Group mapping written to {sg_mapping_path}")


    l.info("Outputs and sg mappings written to files")
    l.info("")
    
    l.info("Script execution complete")
    l.info("Exiting...")
    exit(0)