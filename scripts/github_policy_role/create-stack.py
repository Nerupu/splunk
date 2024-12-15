import boto3 
import subprocess
import os, sys
import logging, json, datetime

from utils import *


timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
stack_name = f"EAF-GITHUB-ROLE-{timestamp}"
cloudformation_template = 'github_role.yaml'
provider_name = 'token.actions.githubusercontent.com'
thumbprint_script = 'get_thumbprint.sh'


def main():
    logging.info("Running github role creation script.")
    region_name = get_environ('AWS_DEFAULT_REGION')
    if not region_name:
        logging.info("ERROR: Missing AWS_DEFAULT_REGION environment variable.")
        sys.exit(1)
    logging.info(f"Region name: {region_name}")

    repo_name = get_environ('REPO_NAME')
    if not repo_name:
        logging.info("Missing REPO_NAME environment variable. Setting to default 'capgemini-car/EAF-Splunk:*")
        repo_name = 'capgemini-car/EAF-Splunk:*'

    logging.info("Creating AWS session.")
    session = boto3.Session(
        aws_access_key_id=get_environ('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=get_environ('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=get_environ('AWS_SESSION_TOKEN'),
        region_name=region_name
    )

    logging.info("")
    logging.info("Fetching AWS account details from Cloud.")
    account = get_aws_account(session)
    logging.info(f"Account ID: {account['Account']}")
    logging.info(f"User ID: {account['UserId']}")
    logging.info(f"Account ARN: {account['Arn']}")

    logging.info("")
    logging.info("Validate stack template...")
    template_body = validate_template(cloudformation_template)
    
    logging.info("")
    logging.info("Check if needed indentity provider exists...")
    id_provider = check_identity_provider(provider_name)
    
    if id_provider:
        logging.info("Identity provider for github role already exists:")
        logging.info(f"Provider URL: {id_provider['Url']}")
        logging.info(f"Audience: {id_provider['ClientIDList']}")
    else:
        logging.info(f"Identity provider for {provider_name} is missing.")
        logging.info(f"Getting thumbprint parameter from {provider_name}..")
        thumbprint = get_thumbprint(thumbprint_script)

        if "OpenSSL not installed" in thumbprint:
            logging.info("ERROR: Missing OpenSSL.. install it and try again.")
            sys.exit(1)
        else:
            logging.info(f"Identity provider {provider_name} will be created in stack.")
    
    logging.info("")
    logging.info("Creating stack...")
    logging.info(f"Stack name: {stack_name}")
    logging.info(f"Stack parameters:")
    logging.info(f"Region: {region_name}")
    logging.info(f"Account ID: {account['Account']}")
    logging.info(f"Thumbprint: {thumbprint if not id_provider else 'False'}")
    logging.info(f"CreateIdentityProvider: {'True' if not id_provider else 'False'}")

    cloudformation_client = boto3.client('cloudformation')
    response = cloudformation_client.create_stack(
        StackName=stack_name,
        TemplateBody=template_body,
        Parameters=[
            {
                'ParameterKey': 'Region',
                'ParameterValue': region_name
            },
            {
                'ParameterKey': 'AccountId',
                'ParameterValue': account['Account']
            },
            {
                'ParameterKey': 'ThumbPrint',
                'ParameterValue': thumbprint if not id_provider else 'False'
            },
            {
                'ParameterKey': 'CreateIdentityProvider',
                'ParameterValue': 'True' if not id_provider else 'False'
            },
            {
                'ParameterKey': 'RepoName',
                'ParameterValue': repo_name
            }
        ],
        Capabilities=[
            'CAPABILITY_IAM',
        ],
    )


    logging.info("Waiting for stack to be created...")
    stack_outputs = wait_until_stack_is_created_and_get_outputs(stack_name, cloudformation_client)
    logging.info("Stack created.")
    logging.info("")
    
    if stack_outputs:
        logging.info("Stack outputs:")
        logging.info("")
        logging.info(json.dumps(stack_outputs, indent=4))
        logging.info("")

    else:
        logging.info("Github role was not created.")


def get_environ(environment_variable=None):
    environment_variable_value = os.environ.get(environment_variable)
    if environment_variable_value:
        return environment_variable_value
    else:
        logging.error(f"Environment variable: '{environment_variable}', is empty or missing!")
        return None


def get_aws_account(session=None):
    client = session.client("sts")

    try:
        account = client.get_caller_identity()
        return account
    except Exception as e:
        logging.error(f"Exception in get_aws_account(): '{e}'")
        sys.exit(6)


def check_identity_provider(name):
    client = boto3.client('iam')
    response = client.list_open_id_connect_providers()
    
    if response:
        for identity in response['OpenIDConnectProviderList']:
            if name in identity['Arn']:
               try:
                    response = client.get_open_id_connect_provider(OpenIDConnectProviderArn=identity['Arn'])
                    return response
               except:
                   return
    return


def get_thumbprint(bash_script):
    
    with open(bash_script, 'r', newline='') as f:
        script_content = f.read().replace('\r\n', '\n')

    temp_script_file = f'TEMP_{bash_script}'
    with open(temp_script_file, 'w', newline='') as f:
        f.write(script_content)

    output = subprocess.run(['bash', temp_script_file], capture_output=True, text=True).stdout
    os.remove(temp_script_file)
    
    return output


def define_logger():
    log_format = logging.Formatter("%(asctime)s\t%(process)s\t%(levelname)s\t%(message)s", "%Y-%m-%d %H:%M:%S")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    out_handler = logging.StreamHandler(sys.stdout)
    out_handler.setLevel(logging.INFO)
    out_handler.setFormatter(log_format)
    logger.addHandler(out_handler)
    return logging


if __name__ == "__main__":
    define_logger()
    main()