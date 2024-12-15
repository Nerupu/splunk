#!/bin/bash

set -e

dev=false

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --dev)
      dev=true
      shift
      ;;
    *)
      echo "Unknown option: $key"
      exit 1
      ;;
  esac
done

CONFIGURATIONS_FOLDER="../json_configurations"
TMP_AREA="./tmp"
INPUT_JSON="config.json"
MIDDLE_JSON="middle.json"
OUTPUT_JSON="output.json"

TMP_AREA=$(readlink -f "$TMP_AREA")
CONFIGURATIONS_FOLDER=$(readlink -f "$CONFIGURATIONS_FOLDER")
echo "Configurations folder: $CONFIGURATIONS_FOLDER"
echo "Tmp area: $TMP_AREA"


CREATE_ARCHITECTURE_SCRIPT_LOCATION="../create_missing_architecture"
CREATE_ARCHITECTURE_SCRIPT_NAME="create_missing_architecture.py"


if [ "$dev" = true ]; then
  echo "Running in local mode"
  cat ../json_configurations/default_architecture_configuration.json > ../json_configurations/config.json
  aws_region=$(cat "${CONFIGURATIONS_FOLDER}/${INPUT_JSON}" | jq -r '.general_parameters.aws_region')
  export AWS_DEFAULT_REGION=$aws_region
fi

input_json=$(cat "${CONFIGURATIONS_FOLDER}/${INPUT_JSON}")

# Create tmp area
if [ -d "$TMP_AREA" ]; then
  echo "Removing tmp area"
  rm -rf "$TMP_AREA"
fi
echo "Creating tmp area"
mkdir "$TMP_AREA"



loglevel=$(echo "$input_json" | jq -r '.general_parameters.loglevel')
name_prefix=$(echo "$input_json" | jq -r '.general_parameters.infrastructure_name_prefix')
region=$(echo "$input_json" | jq -r '.general_parameters.aws_region')
account_id=$(echo "$input_json" | jq -r '.general_parameters.account_id')

vpc_id=$(echo "$input_json" | jq -r '.general_parameters.vpc.id')
vpc_cidr=$(echo "$input_json" | jq -r '.general_parameters.vpc.cidr')
vpc_private_subnet_cidr_az1=$(echo "$input_json" | jq -r '.general_parameters.vpc.private_subnet_cidr_az1')
vpc_private_subnet_cidr_az2=$(echo "$input_json" | jq -r '.general_parameters.vpc.private_subnet_cidr_az2')
vpc_private_subnet_cidr_az3=$(echo "$input_json" | jq -r '.general_parameters.vpc.private_subnet_cidr_az3')
vpc_ipam_pool_id=$(echo "$input_json" | jq -r '.general_parameters.vpc.ipam_pool_id')

access_to_load_balancer_sg_id=$(echo "$input_json" | jq -r '.general_parameters.access_to_load_balancer_sg_id')
kms_key_alias=$(echo "$input_json" | jq -r '.general_parameters.kms_key_alias')

ssm_profile=$(echo "$input_json" | jq -r '.general_parameters.instance_profile.name')
ssm_role_name=$(echo "$input_json" | jq -r '.general_parameters.instance_profile.role_name')
ssm_policy_name=$(echo "$input_json" | jq -r '.general_parameters.instance_profile.policy_name')


if [ "$dev" = true ]; then
  p=python3.10
else
  p=python3
fi

echo "VPC: $vpc_id"
echo "Region: $region"
echo "Python version: $($p --version)"

#get account id from aws sts get-caller-identity
echo "Getting account id from sts get-caller-identity"
sts_account_id=$($p -c "import boto3; print(boto3.client('sts').get_caller_identity().get('Account'))")
if [ "$sts_account_id" != "$account_id" ]; then
  echo "Account id from sts get-caller-identity is different from provided one"
  echo "sts account id: $sts_account_id"
  echo "provided account id: $account_id"
  exit 1
else
  echo "Account id from sts get-caller-identity is the same as provided one"
fi


echo "Creating missing architecture"
echo ""
$p "${CREATE_ARCHITECTURE_SCRIPT_LOCATION}/${CREATE_ARCHITECTURE_SCRIPT_NAME}" \
      --loglevel $loglevel \
      --account-id $account_id \
      --name-prefix $name_prefix \
      --vpc-id "$vpc_id" \
      --vpc-cidr "$vpc_cidr" \
      --private-subnet-cidr-az1 "$vpc_private_subnet_cidr_az1" \
      --private-subnet-cidr-az2 "$vpc_private_subnet_cidr_az2" \
      --private-subnet-cidr-az3 "$vpc_private_subnet_cidr_az3" \
      --ssm-role-name "$ssm_role_name" \
      --ssm-profile-name "$ssm_profile" \
      --ssm-policy-name "$ssm_policy_name" \
      --outputs-location "$TMP_AREA" \
      --access-to-load-balancer-sg-id "$access_to_load_balancer_sg_id" \
      --kms-key-alias "$kms_key_alias" \
      --ipam-pool-id "$vpc_ipam_pool_id" \


echo "Getting info from created architecture"
missing_arch=$(cat "${TMP_AREA}/outputs.json")

updated_input_json=$(echo "$input_json" \
| jq --arg vpc_id "$(echo "$missing_arch" | jq -r '.vpc_id')" \
      --arg private_subnet_az1 "$(echo "$missing_arch" | jq -r '.private_subnet_az1')" \
      --arg private_subnet_az2 "$(echo "$missing_arch" | jq -r '.private_subnet_az2')" \
      --arg private_subnet_az3 "$(echo "$missing_arch" | jq -r '.private_subnet_az3')" \
      --arg ssm_instance_profile "$(echo "$missing_arch" | jq -r '.ssm_instance_profile')" \
      --arg kms_key_id "$(echo "$missing_arch" | jq -r '.kms_key_id')" \
'.general_parameters.vpc.id = $vpc_id
| .general_parameters.kms_key_id = $kms_key_id
| .common_instance_parameters.subnet_az1 = $private_subnet_az1
| .common_instance_parameters.subnet_az2 = $private_subnet_az2
| .common_instance_parameters.subnet_az3 = $private_subnet_az3
| .common_instance_parameters.instance_profile.name = $ssm_instance_profile')
      # --arg s3_bucket_name "$(echo "$missing_arch" | jq -r '.s3_bucket_name')" \
# | .general_parameters.s3_bucket_name = $s3_bucket_name

echo "$updated_input_json" > "${TMP_AREA}/${MIDDLE_JSON}"

echo "Input json updated"
echo "Input json: $updated_input_json"

echo "Security Groups mapping"
cat "${TMP_AREA}/sg_mapping.json"

echo "Running workflow_parse script"
if [ "$dev" = true ]; then
  $p "../workflow_parse/parse_config.py" --workflow-config "${TMP_AREA}/${MIDDLE_JSON}" --security-groups-mapping "${TMP_AREA}/sg_mapping.json" --dev
else
  $p "../workflow_parse/parse_config.py" --workflow-config "${TMP_AREA}/${MIDDLE_JSON}" --security-groups-mapping "${TMP_AREA}/sg_mapping.json"
fi

echo "Removing temporary files"
if [ -d "$TMP_AREA" ]; then
  echo "Removing tmp area"
  rm -rf "$TMP_AREA"
fi