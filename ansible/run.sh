# !/bin/bash
set -e
export S3_BUCKET_NAME='eaf-131213109016-splunk-eu-west-2'
export SPLUNK_ADMIN_PASSWORD='5yfjPk67VjxturLCJki9WvyudAm$ice)'
export SPLUNK_CLUSTER_PASSWORD='dmpitDnTITXgiliz@PttVnwVI6ioim9q'

ENVIRONMENT=dev01
ENVIRONMENT_DIRECTORY=env/$ENVIRONMENT

ansible-playbook -i $ENVIRONMENT_DIRECTORY site.yaml

# aws ssm start-session --target i-0bc83d125a450520c --document-name AWS-StartPortForwardingSession --parameters '{"portNumber":["8000"],"localPortNumber":["8000"]}'