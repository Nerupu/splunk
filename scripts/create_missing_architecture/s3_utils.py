import boto3, logging, json
from utils import validate_template, wait_until_stack_is_created_and_get_outputs
import re

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

def validate_bucket_name(bucket_name, l:logging.Logger = logging.getLogger(__name__)):
    name_is_valid = True
    # Check if bucket name length is between 3 and 63 characters
    if len(bucket_name) < 3 or len(bucket_name) > 63:
        l.error(f"Bucket name {bucket_name} has less than 3 or more than 63 characters.")
        name_is_valid = False

    # Check if bucket name starts and ends with a lowercase letter or number
    if not re.match('^[a-z0-9].*[a-z0-9]$', bucket_name):
        l.error(f"Bucket name {bucket_name} does not start and end with a lowercase letter or number.")
        name_is_valid = False

    # Check if bucket name contains only lowercase letters, numbers, periods, and hyphens
    if not re.match('^[a-z0-9.-]*$', bucket_name):
        l.error(f"Bucket name {bucket_name} contains characters other than lowercase letters, numbers, periods, and hyphens.")
        name_is_valid = False

    # Check if bucket name contains consecutive periods or hyphens, or period and hyphen together
    if re.search('(\.\.)|(\-\-)|(\.-)|(-\.)', bucket_name):
        l.error(f"Bucket name {bucket_name} contains consecutive periods or hyphens, or period and hyphen together.")
        name_is_valid = False

    # Check if bucket name follows the IPv4-like address pattern
    if re.match('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', bucket_name):
        l.error(f"Bucket name {bucket_name} follows the IPv4-like address pattern.")
        name_is_valid = False

    # Check if bucket name contains uppercase letters
    if re.search('[A-Z]', bucket_name):
        l.error(f"Bucket name {bucket_name} contains uppercase letters.")
        name_is_valid = False

    # Check if bucket name contains underscores
    if re.search('_', bucket_name):
        l.error(f"Bucket name {bucket_name} contains underscores.")
        name_is_valid = False

    # Check if bucket name contains adjacent symbols
    if re.search('[-.]{2,}', bucket_name):
        l.error(f"Bucket name {bucket_name} contains adjacent symbols.")
        name_is_valid = False

    # Check if bucket name has a hyphen next to a period, e.g., "my-.bucket"
    if re.search('\.-|-\.', bucket_name):
        l.error(f"Bucket name {bucket_name} has a hyphen next to a period.")
        name_is_valid = False

    return name_is_valid

def generate_bucket_name(
    environment_prefix:str = 'prod',
    account_id:str = None,
    software:str = 'splunk', 
    l:logging.Logger = logging.getLogger(__name__)
):
    # $PREFIX-$ACCOUNT_ID-eaf-$SOFTWARE

    # Where
    # $PREFIX can stand for prod/dev/test depending on use. This value should be taken from flow
    # $ACCOUNT_ID should be AWS account ID, which will ensure that name will be unique
    # $SOFTWARE can be taken from hardcoded varfiable (or passed via flow), for this use: splunk
    if account_id is None:
        account_id = boto3.client('sts').get_caller_identity().get('Account')

    region = boto3.session.Session().region_name

    bucket_name = f"{environment_prefix}-{account_id}-eaf-{software}-{region}"
    if validate_bucket_name(bucket_name):
        return bucket_name
    else:
        l.error(f"Environment prefix: {environment_prefix}")
        l.error(f"Account ID: {account_id}")
        l.error(f"Software: {software}")
        l.error(f"Region: {region}")
        l.error(f"Generated bucket name: {bucket_name}")
        l.error(f"Generated bucket name {bucket_name} is not valid.")

        raise Exception(f"Generated bucket name {bucket_name} is not valid.")

def create_s3_bucket(
        stack_name:str,
        vpc_id:str,
        l:logging.Logger = logging.getLogger(__name__)
):
    bucket_name = generate_bucket_name(l=l)

    l.info(f"Checking if bucket with bucket name \"{bucket_name}\" already exist...")

    if check_if_bucket_alerady_exist(bucket_name, l):
        return bucket_name
    
    l.info("Creating bucket...")

    cloudformation_client = boto3.client('cloudformation')
    template_body = validate_template('cf_s3_bucket.yaml')

    l.info("+"*100)
    l.info("Creating stack with following parameters:")
    l.info("")
    l.info(f"Stack name: {stack_name}")
    l.info(f"VPC ID: {vpc_id}")
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
                'ParameterKey': 'BucketName',
                'ParameterValue': bucket_name
            },
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
    l.debug("Stack outputs:")
    l.debug("")
    l.debug(json.dumps(stack_outputs, indent=4))
    l.debug("")
    l.info("+"*100)

    return stack_outputs['BucketName']