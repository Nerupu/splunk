
import json

# Your JSON data
data =  {
    "aws_region": "eu-central-1",
    "account_id": "***",
    "kms_key_id": "bb18f3e1-4df6-45fb-b1b2-dd18e9dfe076",
    "instances_list": [
        {
            "vm_instance_type": "t3.xlarge",
            "vm_ami_name": "CCP Hardened Amazon Linux 2*",
            "vm_instance_profile": "ec2-instance-access",
            "vm_worker_type": "SearchHead",
            "vm_sg_list": "<Replace with Security Group ID>",
            "vm_tags": {
                "required": {
                    "environment": "dev",
                    "product": "splunk",
                    "application": "splunk",
                    "ccp_managed": "core",
                    "compliance": "test",
                    "data_residency": "eea",
                    "instance": "eu",
                    "business_unit": "test1",
                    "type": "<required value>",
                    "type2": "MonitoringConsole"
                },
                "type3": "MonitoringConsole"
            },
            "vm_subnet": "<Replace with Subnet ID>",
            "vm_name": "euwaa-eafsshd001",
            "root_volume": {
                "volume_size": "20",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            },
            "data_volumes": {
                "/dev/sdf": {
                    "mount_point": "/opt/splunk",
                    "volume_size": "15",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                },
                "/dev/xvdg": {
                    "mount_point": "/mnt/data1",
                    "volume_size": "10",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                },
                "/dev/xvdh": {
                    "mount_point": "/mnt/data2",
                    "volume_size": "10",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                }
            }
        },
        {
            "vm_instance_type": "t3.xlarge",
            "vm_ami_name": "CCP Hardened Amazon Linux 2*",
            "vm_instance_profile": "ec2-instance-access",
            "vm_worker_type": "SearchHead",
            "vm_sg_list": "<Replace with Security Group ID>",
            "vm_tags": {
                "required": {
                    "environment": "dev",
                    "product": "splunk",
                    "application": "splunk",
                    "ccp_managed": "core",
                    "compliance": "test",
                    "data_residency": "eea",
                    "instance": "eu",
                    "business_unit": "test1",
                    "type": "<required value>",
                    "type2": "MonitoringConsole"
                },
                "type3": "MonitoringConsole"
            },
            "vm_subnet": "<Replace with Subnet ID>",
            "vm_name": "euwaa-eafsshd002",
            "root_volume": {
                "volume_size": "20",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            },
            "data_volumes": {
                "/dev/sdf": {
                    "mount_point": "/opt/splunk",
                    "volume_size": "15",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                }
            }
        },
        {
            "vm_instance_type": "t3.xlarge",
            "vm_ami_name": "CCP Hardened Amazon Linux 2*",
            "vm_instance_profile": "ec2-instance-access",
            "vm_worker_type": "SearchHead",
            "vm_sg_list": "<Replace with Security Group ID>",
            "vm_tags": {
                "required": {
                    "environment": "dev",
                    "product": "splunk",
                    "application": "splunk",
                    "ccp_managed": "core",
                    "compliance": "test",
                    "data_residency": "eea",
                    "instance": "eu",
                    "business_unit": "test1",
                    "type": "<required value>",
                    "type2": "MonitoringConsole"
                },
                "type3": "MonitoringConsole"
            },
            "vm_subnet": "<Replace with Subnet ID>",
            "vm_name": "euwaa-eafsshd003",
            "root_volume": {
                "volume_size": "20",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            },
            "data_volumes": {
                "/dev/sdf": {
                    "mount_point": "/opt/splunk",
                    "volume_size": "15",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                }
            }
        },
        {
            "vm_instance_type": "t3.medium",
            "vm_ami_name": "CCP Hardened Amazon Linux 2*",
            "vm_instance_profile": "ec2-instance-access",
            "vm_worker_type": "Indexer",
            "vm_sg_list": "<Replace with Security Group ID>",
            "vm_tags": {
                "required": {
                    "environment": "dev",
                    "product": "splunk",
                    "application": "splunk",
                    "ccp_managed": "core",
                    "compliance": "test",
                    "data_residency": "eea",
                    "instance": "eu",
                    "business_unit": "test1",
                    "type": "<required value>",
                    "type2": "MonitoringConsole"
                },
                "type3": "MonitoringConsole"
            },
            "vm_subnet": "<Replace with Subnet ID>",
            "vm_name": "euwaa-eafsixd001",
            "root_volume": {
                "volume_size": "50",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            },
            "data_volumes": {
                "/dev/sdf": {
                    "mount_point": "/opt/splunk",
                    "volume_size": "15",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                }
            }
        },
        {
            "vm_instance_type": "t3.medium",
            "vm_ami_name": "CCP Hardened Amazon Linux 2*",
            "vm_instance_profile": "ec2-instance-access",
            "vm_worker_type": "Indexer",
            "vm_sg_list": "<Replace with Security Group ID>",
            "vm_tags": {
                "required": {
                    "environment": "dev",
                    "product": "splunk",
                    "application": "splunk",
                    "ccp_managed": "core",
                    "compliance": "test",
                    "data_residency": "eea",
                    "instance": "eu",
                    "business_unit": "test1",
                    "type": "<required value>",
                    "type2": "MonitoringConsole"
                },
                "type3": "MonitoringConsole"
            },
            "vm_subnet": "<Replace with Subnet ID>",
            "vm_name": "euwaa-eafsixd002",
            "root_volume": {
                "volume_size": "50",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            },
            "data_volumes": {
                "/dev/sdf": {
                    "mount_point": "/opt/splunk",
                    "volume_size": "15",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                }
            }
        },
        {
            "vm_instance_type": "t3.medium",
            "vm_ami_name": "CCP Hardened Amazon Linux 2*",
            "vm_instance_profile": "ec2-instance-access",
            "vm_worker_type": "Indexer",
            "vm_sg_list": "<Replace with Security Group ID>",
            "vm_tags": {
                "required": {
                    "environment": "dev",
                    "product": "splunk",
                    "application": "splunk",
                    "ccp_managed": "core",
                    "compliance": "test",
                    "data_residency": "eea",
                    "instance": "eu",
                    "business_unit": "test1",
                    "type": "<required value>",
                    "type2": "MonitoringConsole"
                },
                "type3": "MonitoringConsole"
            },
            "vm_subnet": "<Replace with Subnet ID>",
            "vm_name": "euwaa-eafsixd003",
            "root_volume": {
                "volume_size": "50",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            },
            "data_volumes": {
                "/dev/sdf": {
                    "mount_point": "/opt/splunk",
                    "volume_size": "15",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                }
            }
        },
        {
            "vm_instance_type": "t3.medium",
            "vm_ami_name": "CCP Hardened Amazon Linux 2*",
            "vm_instance_profile": "ec2-instance-access",
            "vm_worker_type": "Forwarder",
            "vm_sg_list": "<Replace with Security Group ID>",
            "vm_tags": {
                "required": {
                    "environment": "dev",
                    "product": "splunk",
                    "application": "splunk",
                    "ccp_managed": "core",
                    "compliance": "test",
                    "data_residency": "eea",
                    "instance": "eu",
                    "business_unit": "test1",
                    "type": "<required value>",
                    "type2": "MonitoringConsole"
                },
                "type3": "MonitoringConsole"
            },
            "vm_subnet": "<Replace with Subnet ID>",
            "vm_name": "euwaa-eafsfwd001",
            "root_volume": {
                "volume_size": "20",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            },
            "data_volumes": {
                "/dev/sdf": {
                    "mount_point": "/opt/splunk",
                    "volume_size": "15",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                }
            }
        },
        {
            "vm_instance_type": "t3.medium",
            "vm_ami_name": "CCP Hardened Amazon Linux 2*",
            "vm_instance_profile": "ec2-instance-access",
            "vm_worker_type": "Forwarder",
            "vm_sg_list": "<Replace with Security Group ID>",
            "vm_tags": {
                "required": {
                    "environment": "dev",
                    "product": "splunk",
                    "application": "splunk",
                    "ccp_managed": "core",
                    "compliance": "test",
                    "data_residency": "eea",
                    "instance": "eu",
                    "business_unit": "test1",
                    "type": "<required value>",
                    "type2": "MonitoringConsole"
                },
                "type3": "MonitoringConsole"
            },
            "vm_subnet": "<Replace with Subnet ID>",
            "vm_name": "euwaa-eafsfwd002",
            "root_volume": {
                "volume_size": "20",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            },
            "data_volumes": {
                "/dev/sdf": {
                    "mount_point": "/opt/splunk",
                    "volume_size": "15",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                }
            }
        },
        {
            "vm_instance_type": "t3.medium",
            "vm_ami_name": "CCP Hardened Amazon Linux 2*",
            "vm_instance_profile": "ec2-instance-access",
            "vm_worker_type": "Forwarder",
            "vm_sg_list": "<Replace with Security Group ID>",
            "vm_tags": {
                "required": {
                    "environment": "dev",
                    "product": "splunk",
                    "application": "splunk",
                    "ccp_managed": "core",
                    "compliance": "test",
                    "data_residency": "eea",
                    "instance": "eu",
                    "business_unit": "test1",
                    "type": "<required value>",
                    "type2": "MonitoringConsole"
                },
                "type3": "MonitoringConsole"
            },
            "vm_subnet": "<Replace with Subnet ID>",
            "vm_name": "euwaa-eafsfwd003",
            "root_volume": {
                "volume_size": "20",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            },
            "data_volumes": {
                "/dev/sdf": {
                    "mount_point": "/opt/splunk",
                    "volume_size": "15",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                }
            }
        },
        {
            "vm_instance_type": "t3.medium",
            "vm_ami_name": "CCP Hardened Amazon Linux 2*",
            "vm_instance_profile": "ec2-instance-access",
            "vm_worker_type": "LicenseServer",
            "vm_sg_list": "<Replace with Security Group ID>",
            "vm_tags": {
                "required": {
                    "environment": "dev",
                    "product": "splunk",
                    "application": "splunk",
                    "ccp_managed": "core",
                    "compliance": "test",
                    "data_residency": "eea",
                    "instance": "eu",
                    "business_unit": "test1",
                    "type": "<required value>",
                    "type2": "MonitoringConsole"
                },
                "type3": "MonitoringConsole"
            },
            "vm_subnet": "<Replace with Subnet ID>",
            "vm_name": "euwaa-eafslsd001",
            "root_volume": {
                "volume_size": "20",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            },
            "data_volumes": {
                "/dev/sdf": {
                    "mount_point": "/opt/splunk",
                    "volume_size": "15",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                }
            }
        },
        {
            "vm_instance_type": "t3.medium",
            "vm_ami_name": "CCP Hardened Amazon Linux 2*",
            "vm_instance_profile": "ec2-instance-access",
            "vm_worker_type": "Master",
            "vm_sg_list": "<Replace with Security Group ID>",
            "vm_tags": {
                "required": {
                    "environment": "dev",
                    "product": "splunk",
                    "application": "splunk",
                    "ccp_managed": "core",
                    "compliance": "test",
                    "data_residency": "eea",
                    "instance": "eu",
                    "business_unit": "test1",
                    "type": "<required value>",
                    "type2": "MonitoringConsole"
                },
                "type3": "MonitoringConsole"
            },
            "vm_subnet": "<Replace with Subnet ID>",
            "vm_name": "euwaa-eafsmsd001",
            "root_volume": {
                "volume_size": "20",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            },
            "data_volumes": {
                "/dev/sdf": {
                    "mount_point": "/opt/splunk",
                    "volume_size": "15",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                }
            }
        },
        {
            "vm_instance_type": "t3.medium",
            "vm_ami_name": "CCP Hardened Amazon Linux 2*",
            "vm_instance_profile": "ec2-instance-access",
            "vm_worker_type": "Deploy",
            "vm_sg_list": "<Replace with Security Group ID>",
            "vm_tags": {
                "required": {
                    "environment": "dev",
                    "product": "splunk",
                    "application": "splunk",
                    "ccp_managed": "core",
                    "compliance": "test",
                    "data_residency": "eea",
                    "instance": "eu",
                    "business_unit": "test1",
                    "type": "<required value>",
                    "type2": "MonitoringConsole"
                },
                "type3": "MonitoringConsole"
            },
            "vm_subnet": "<Replace with Subnet ID>",
            "vm_name": "euwaa-eafsdpd001",
            "root_volume": {
                "volume_size": "20",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            },
            "data_volumes": {
                "/dev/sdf": {
                    "mount_point": "/opt/splunk",
                    "volume_size": "15",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                }
            }
        },
        {
            "vm_instance_type": "t3.medium",
            "vm_ami_name": "CCP Hardened Amazon Linux 2*",
            "vm_instance_profile": "ec2-instance-access",
            "vm_worker_type": "DeploymentServer",
            "vm_sg_list": "<Replace with Security Group ID>",
            "vm_tags": {
                "required": {
                    "environment": "dev",
                    "product": "splunk",
                    "application": "splunk",
                    "ccp_managed": "core",
                    "compliance": "test",
                    "data_residency": "eea",
                    "instance": "eu",
                    "business_unit": "test1",
                    "type": "<required value>",
                    "type2": "MonitoringConsole"
                },
                "type3": "MonitoringConsole"
            },
            "vm_subnet": "<Replace with Subnet ID>",
            "vm_name": "euwaa-eafsdsd001",
            "root_volume": {
                "volume_size": "20",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            },
            "data_volumes": {
                "/dev/sdf": {
                    "mount_point": "/opt/splunk",
                    "volume_size": "15",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                }
            }
        },
        {
            "vm_instance_type": "t3.medium",
            "vm_ami_name": "CCP Hardened Amazon Linux 2*",
            "vm_instance_profile": "ec2-instance-access",
            "vm_worker_type": "MonitoringConsole",
            "vm_sg_list": "<Replace with Security Group ID>",
            "vm_tags": {
                "required": {
                    "environment": "dev",
                    "product": "splunk",
                    "application": "splunk",
                    "ccp_managed": "core",
                    "compliance": "test",
                    "data_residency": "eea",
                    "instance": "eu",
                    "business_unit": "test1",
                    "type": "<required value>",
                    "type2": "MonitoringConsole"
                },
                "type3": "MonitoringConsole"
            },
            "vm_subnet": "<Replace with Subnet ID>",
            "vm_name": "euwaa-eafsmcd001",
            "root_volume": {
                "volume_size": "20",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            },
            "data_volumes": {
                "/dev/sdf": {
                    "mount_point": "/opt/splunk",
                    "volume_size": "15",
                    "volume_type": "gp3",
                    "delete_on_termination": "true",
                    "iops": "3000",
                    "throughput": "125"
                }
            }
        }
    ]
}

# Define the new tag value


# Create a dictionary to map vm_worker_type to the new tag value
worker_type_to_tag_mapping = {
    "SearchHead": "SearchHead",
    "Indexer": "Indexer",
    "Forwarder": "Forwarder",
    "LicenseServer": "LicenseServer",
    "Master": "Master",
    "Deploy": "Deploy",
    "DeploymentServer": "DeploymentServer",
    "MonitoringConsole": "MonitoringConsole",
}

# Iterate through the instances and update the "type" tag based on vm_worker_type
for instance in data["instances_list"]:
    worker_type = instance["vm_worker_type"]
    if worker_type in worker_type_to_tag_mapping:
        instance["vm_tags"]["required"]["type"] = worker_type_to_tag_mapping[worker_type]

# Serialize the updated data back to JSON
updated_json = json.dumps(data, indent=4)

# Print or save the updated JSON
print(updated_json)
