import logging
import time
import boto3
import botocore
from pprint import pprint

DESIRED_STACK_STATUS = "CREATE_COMPLETE"
MAX_RETRIES = 200
RETRY_INTERVAL_SECONDS = 5
DELETE_IF_FAILED = True


def get_stack_status(stack_name):
    cloudformation_client = boto3.client('cloudformation')
    try:
        stack = cloudformation_client.describe_stacks(StackName=stack_name)['Stacks'][0]
        stack_status = stack['StackStatus']
        return stack_status
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError':
            response = cloudformation_client.list_stacks(
                        StackStatusFilter=['DELETE_COMPLETE']
                    )

            deleted_stacks = [stack['StackName'] for stack in response['StackSummaries']]

            if stack_name in deleted_stacks:
                return "DELETE_COMPLETE"
            else:
                raise e
        else:
            raise e

        
def wait_until_stack_reaches_status(stack_name:str, desired_status:str = DESIRED_STACK_STATUS, l: logging.Logger = logging.getLogger(__name__)):
    retry = 0

    stack_status = get_stack_status(stack_name)
    if stack_status == desired_status:
        l.info("")
        l.info(f"Stack {stack_name} has already reached the desired status: {desired_status}")
        l.info("")
        return stack_status
    
    l.info("")
    l.info(f"Waiting for stack {stack_name} to reach the desired status: {desired_status}...")
    l.info(f"Max retries: {MAX_RETRIES}, retry interval: {RETRY_INTERVAL_SECONDS} seconds, max time: {MAX_RETRIES*RETRY_INTERVAL_SECONDS} seconds...")
    l.info("")

    s = time.time()
    while retry < MAX_RETRIES:
        stack_status = get_stack_status(stack_name)
        l.info(f"Stack status: {stack_status}. Elapsed time {time.time() - s:.2f} seconds. Retry {retry}/{MAX_RETRIES}")

        if stack_status == "ROLLBACK_IN_PROGRESS" and desired_status != "ROLLBACK_COMPLETE":
            l.info(f"Stack {stack_name} is rolling back. Current status: {stack_status}")
            break

        if stack_status == desired_status:
            l.info(f"Stack {stack_name} has reached the desired status: {desired_status}")
            break

        if "IN_PROGRESS" not in stack_status:
            l.info(f"Stack {stack_name} is no longer running. Current status: {stack_status}")
            break
            
        retry += 1
        time.sleep(RETRY_INTERVAL_SECONDS)

    l.info("")
    
    if retry == MAX_RETRIES:
        l.error(f"Stack {stack_name} has not reached the desired status: {DESIRED_STACK_STATUS} within {MAX_RETRIES} retries which took {MAX_RETRIES*RETRY_INTERVAL_SECONDS} seconds")
        l.error("Please check the CloudFormation console for more details.")
        l.error("Exiting...")
        exit(1)

    return stack_status


def display_stack_events(stack_name: str, cloudformation_client, l: logging.Logger = logging.getLogger(__name__)):
    l.info(f"Displaying stack events for {stack_name}:")

    events = cloudformation_client.describe_stack_events(StackName=stack_name)['StackEvents']

    l.debug("Events:")
    l.debug(events)

    for event in events[::-1]:
        l.info("========================================")
        l.info(f"EventId: {event['EventId']}")
        l.info(f"Timestamp: {event['Timestamp']}")
        l.info(f"ResourceType: {event['ResourceType']}")
        l.info(f"LogicalResourceId: {event['LogicalResourceId']}")
        l.info(f"ResourceStatus: {event['ResourceStatus']}")
        l.info(f"ResourceStatusReason: {event.get('ResourceStatusReason', 'N/A')}")
        l.info("========================================")
        l.info("")


def wait_until_stack_is_created_and_get_outputs(stack_name:str, delete_if_failed:bool = True, l: logging.Logger = logging.getLogger(__name__)) -> None:
    cloudformation_client = boto3.client('cloudformation')

    stack_status = wait_until_stack_reaches_status(stack_name)

    if stack_status != DESIRED_STACK_STATUS:
        l.info("")
        l.info(f"Stack {stack_name} has not reached the desired status: {DESIRED_STACK_STATUS} it instead reached the status: {stack_status}")
        l.info("")
        l.info("Displaying stack events:")
        display_stack_events(stack_name, cloudformation_client, l)
        l.info("")

        stack_status = wait_until_stack_reaches_status(stack_name, "ROLLBACK_COMPLETE")

        l.info("")
        l.info(f"Stack {stack_name} has reached the status: {stack_status}")
        l.info("")
        l.info("Displaying stack events:")
        display_stack_events(stack_name, cloudformation_client, l)
        l.info("")

        if (stack_status == "CREATE_FAILED" or stack_status == "ROLLBACK_COMPLETE") and delete_if_failed:
            l.info("")
            l.error(f"Stack {stack_name} has failed to create. Deleting the stack...")
            # Delete the failed stack
            cloudformation_client.delete_stack(StackName=stack_name)

            # Wait until the stack is deleted
            stack_status = wait_until_stack_reaches_status(stack_name, "DELETE_COMPLETE")

            if stack_status == "DELETE_COMPLETE":
                l.info(f"Stack {stack_name} has been successfully deleted.")
            else:
                l.error(f"Stack {stack_name} has failed to delete. It has status {stack_status}. Please delete the stack manually.")

            l.info("Exiting...")
            exit(1)
        elif not delete_if_failed:
            l.info("")
            l.error(f"Stack {stack_name} has failed to create and delete_if_failed is set to False. Please delete the stack manually.")
            l.info("Exiting...")
            exit(1)

    elif not delete_if_failed and "ROLLBACK" in stack_status:
        l.info("")
        l.error(f"Stack {stack_name} has failed to create. Please delete the stack manually.")
        l.info("Exiting...")
        exit(1)
    else:

        # Describe the stack and get the outputs
        stack = cloudformation_client.describe_stacks(StackName=stack_name)['Stacks'][0]

        if 'Outputs' in stack:
            stack_outputs = stack['Outputs']
        else:
            stack_outputs = None

        l.info("")
        l.info(f"Stack {stack_name} has been successfully created.")
        if stack_outputs:
            l.debug("Stack outputs:")
            l.debug("")

            # l.info the outputs
            for output in stack_outputs:
                l.debug(f"Output Key: {output['OutputKey']}")
                l.debug(f"Output Value: {output['OutputValue']}")
                l.debug("")
            # Convert the outputs to a dictionary

            stack_outputs = {output['OutputKey']: output['OutputValue'] for output in stack_outputs}

        # Return the outputs
        return stack_outputs


def validate_template(template_name: str, l: logging.Logger = logging.getLogger(__name__)) -> str:
        cloudformation_client = boto3.client('cloudformation')
        
        try:
            with open(template_name, 'r') as f:
                template_body = f.read()
        except Exception as e:
            l.error(f"Could not open template {template_name}")
            l.error(e)
            exit(1)
        
        
        l.info("Validating template")
        try:
            response = cloudformation_client.validate_template(TemplateBody=template_body)  
            if l.level == logging.DEBUG:
                pprint(response)
        except botocore.exceptions.ClientError as e:
            l.error("Template is not valid")
            l.error(e)
            exit(1)
        l.info("Template is valid")
        return template_body

