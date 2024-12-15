import boto3

def get_latest_amazon_linux_ami(ami_name, virtualization_type, root_device_type, architecture):
    # Create an EC2 resource object
    ec2_resource = boto3.resource('ec2')

    # Define the filter conditions
    filters = [
        {
            'Name': 'name',
            'Values': [f"*{ami_name}*"]
        },
        {
            'Name': 'virtualization-type',
            'Values': [virtualization_type]
        },
        {
            'Name': 'root-device-type',
            'Values': [root_device_type]
        },
        {
            'Name': 'architecture',
            'Values': [architecture]
        }
    ]

    # Concatenate the owners list
    owners = ["self", "amazon"]

    # Retrieve the most recent AMI matching the filters
    response = ec2_resource.images.filter(Owners=owners, Filters=filters)

    # Sort the images by creation date in descending order
    sorted_images = sorted(response, key=lambda x: x.creation_date, reverse=True)

    # Extract and return the latest AMI ID and name
    latest_ami_id = sorted_images[0].id if sorted_images else None
    latest_ami_name = sorted_images[0].name if sorted_images else None
    return latest_ami_id, latest_ami_name

# Example usage
ami_name = "Amazon Linux 2023"
ami_architecture = "x86_64"
ami_root_device_type = "ebs"
ami_virtualization_type = "hvm"

latest_ami_id, latest_ami_name = get_latest_amazon_linux_ami(ami_name, ami_virtualization_type, ami_root_device_type, ami_architecture)
print("Latest AMI ID:", latest_ami_id)
print("Latest AMI Name:", latest_ami_name)
