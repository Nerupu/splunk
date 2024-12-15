
import os
import git
import boto3

# GitHub repository URL
github_repo_url = "https://github.com/capgemini-car/EAF-Splunk-WIP.git"

# Local path to clone the repository
local_path = "splunk/deploymentServer/default_app/v1/"

# AWS credentials and region
aws_access_key_id = 'your_access_key'
aws_secret_access_key = 'your_secret_key'
aws_region = 'us-west-2'  # Specify your desired AWS region

# S3 bucket information
s3_bucket_name = 'eaf-splunk-binaries-858165505743- eu-central-1'
s3_key = "s3/path/to/store/content/"

# Clone the GitHub repository to the local path
repo = git.Repo.clone_from(github_repo_url, local_path)

# Initialize an S3 client
s3 = boto3.client('s3', region_name=aws_region)

# Function to upload files to S3
def upload_files_to_s3(local_dir, s3_bucket, s3_prefix):
    for root, dirs, files in os.walk(local_dir):
        for file in files:
            local_file_path = os.path.join(root, file)
            s3_file_path = s3_prefix + os.path.relpath(local_file_path, local_dir)
            s3.upload_file(local_file_path, s3_bucket, s3_file_path)
            print(f"Uploaded {local_file_path} to S3 as {s3_file_path}")

# Upload the cloned content to the specified S3 bucket
upload_files_to_s3(local_path, s3_bucket_name, s3_key)

print("Content uploaded to S3.")
