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
INPUT_JSON="config.json"

input_json_path="${CONFIGURATIONS_FOLDER}/${INPUT_JSON}"
input_json_content=$(cat "$input_json_path")

if [ "$dev" = true ]; then
  echo "Running in dev mode"
  cat ../json_configurations/default_splunk_configuration.json > ../json_configurations/config.json
  aws_region=$(echo $input_json | jq -r '.general_parameters.aws_region')
  export AWS_DEFAULT_REGION=$aws_region
  p=python3.10
else
  p=python3
fi

echo "Python version: $($p --version)"

echo "Starton creation of architecture"

$p "./create_architecture.py" --config-path "$input_json_path"