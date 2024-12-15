# Construction of input JSON

Here is an overview of all parameters that need to be provided in JSON for deployment to work. Construction of keys and objects has to remen as described below. Values should be changed according to your needs.

## Common parameters

Before delving into details of each field, there are some important assumpions that are easier to explain beforehad than in each field description.

To properly deploy all instances you would have normally define each parameters of deployment for each instance separately. To improve this process, we introduced common_instance_parameters object. This object contains all parameters that are common for all instances. This way you can define them once and then only define parameters that are specific for each instance.

After defining common parameters you need to provide objects for each instance. They do not have to include all parameters, only those that are different from common parameters. Only field that you need to specify for each instance is worker_type.

## Tags

To pass tags in input JSON you need to define them in following structure eather in common_instance_parameters or in instance object:

```json
"tags": {
    "required" : {
        "environment" : "dev",
        "product" : "splunk",
        "application" : "splunk",
        "ccp_managed" : "core",
        "compliance" : "test",
        "data_residency" : "eea",
        "instance" : "uk",
        "business_unit": "test1"
    },
    "optional": {
        "example_key" : "example_value"
    }
}
```

Required tags are mandatory and are following: environment, product, application, ccp_managed, compliance, data_residency, instance, business_unit. Valid values for those tags can be cheked in `EAF-Splunk\scripts\workflow_parse\tag_validation.json`.

Optional tags are optional and can be added if needed. Anything passed in optional tags will be added to instance tags.

## Data volumes

Data volumes are defined in following structure:

```json
"data_volumes": [
            {
            "mount_point": "/mnt/data2",
            "volume_size": "10",
            "volume_type": "gp3",
            "delete_on_termination": "true",
            "iops": "3000",
            "throughput": "125"
        }
]
```

Under the data_volumes key you need to define list of objects. Each object represents one data volume. You can define as many data volumes as you want. Each data volume object needs to have following fields:

- mount_point - mount point of data volume, e.g. /mnt/data2
- volume_size - size of data volume in GB, e.g. 10
- volume_type - type of data volume, e.g. gp3
- delete_on_termination - if set to true, data volume will be deleted when instance is terminated, reccoemnded is true
- iops - only for volume type that supports iops parameters, e.g. 3000
- throughput - only for volume type that supports throughput parameter, e.g. 125

All of those parameters should be passed as strings.

## Explanation of parameters

```json
{
    "workflow_parameters":{
        "github_role_arn": "role of GitHub Role created by github_role.yaml or script in github_policy_role folder",
    },
    "general_parameters": {
        "account_id": "account id for sanity checks",
        "aws_region": "region where you want to deploy infrastructure",
        "loglevel": "loglevel for python scripts, valid values are: debug, info, warning, error, critical, recommended is info",
        "infrastructure_name_prefix": "prefix for infrastructure related resources, e.g. VPC, Subnets, Security Groups, etc.; recommended is 'EAF'",
        "vpc": {
            "id": "can be 'create' or accual vpc id, if 'create' is provided, new vpc will be created, otherwise existing vpc will be used",
            "cidr": "cidr block for vpc, e.g. 10.0.0.0/16",
            "public_subnet_cidr": "cidr block for public subnets, e.g. 10.0.1.0/24",
            "private_subnet_cidr_az1": "cidr block for private subnets AZ1, e.g. 10.0.2.0/24",
            "private_subnet_cidr_az2": "cidr block for private subnets AZ2, e.g. 10.0.3.0/24",
            "private_subnet_cidr_az3": "cidr block for private subnets AZ3, e.g. 10.0.4.0/24"
        },
        "access_to_load_balancer_sg_id": "id of security group that will be allowed to access load balancer, load balancer is main acccess point to splunk ui and traffic, e.g. sg-1234567890abcdefg",
        "instances_quantity": "sanity check variable, this need to be provided as int, withou parenthesis, e.g. 12, this means that later you will need to provide 12 specifications for workers",
        "load_balancer": {  
            "tags" : {
                "environment": "dev",
                "product": "splunk",
                "application": "splunk",
                "ccp_managed": "core",
                "compliance": "test",
                "data_residency": "eea",
                "instance": "uk",
                "business_unit": "test1"
            } 
        },
        "instance_profile": {
            "name": "name of instance profile for ssm, recommended: SSMInstanceProfile",
            "role_name": "name of role, recommended: SSMRole",
            "policy_name": "name of policy attached to role for ssm, recommended: AnsiblePolicy"
        }
    },
    "common_instance_parameters": {
        "instance_type": "type of an aws instance, e.g. t2.small, t2.medium, t2.large, etc.; all standard types in AWS should be supported",
        "ami_name": "Amazon Linux 2",
        "worker_type": "sanity check variable, here this should be set to something that is not supported, e.g. 'unset', then if you forget to set some worker_type, you will get error message",
        "tags": {
            "required" : {
                "environment" : "dev",
                "product" : "splunk",
                "application" : "splunk",
                "ccp_managed" : "core",
                "compliance" : "test",
                "data_residency" : "eea",
                "instance" : "uk",
                "business_unit": "test1"
            }
        },
        "root_volume": {
            "volume_size": "root volume size in GB, e.g. 20",
            "volume_type": "root volume type, e.g. gp3, gp2, io1, etc., reccoemnded is gp3",
            "delete_on_termination": "true or false, recommended is true"
        },
        "data_volumes": []
    },
    "specifications_per_worker": [
        {
            "worker_type": "search-head",
            "instance_type": "t2.small",
            "data_volumes": [
                    {
                        "mount_point": "/mnt/data1",
                        "volume_size": "100",
                        "volume_type": "gp3",
                        "delete_on_termination": "true",
                        "iops": "3000",
                        "throughput": "125"
                    },
                    {
                        "mount_point": "/mnt/data2",
                        "volume_size": "10",
                        "volume_type": "gp3",
                        "delete_on_termination": "true",
                        "iops": "3000",
                        "throughput": "125"
                    }
                ]
        },
        {
            "worker_type": "search-head",
            "instance_type": "t2.small"
        },
        {
            "worker_type": "search-head",
            "instance_type": "t2.small"
        },
        {
            "worker_type": "indexer",
            "instance_type": "t2.small",
            "root_volume": {
                "volume_size": "50",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            }
        },
        {
            "worker_type": "indexer",
            "instance_type": "t2.small",
            "root_volume": {
                "volume_size": "50",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            }
        },
        {
            "worker_type": "indexer",
            "instance_type": "t2.small",
            "root_volume": {
                "volume_size": "50",
                "volume_type": "gp3",
                "delete_on_termination": "true"
            }
        },
        {
            "worker_type": "forwarder",
            "instance_type": "t2.small"
        },
        {
            "worker_type": "forwarder",
            "instance_type": "t2.small"
        },
        {
            "worker_type": "forwarder",
            "instance_type": "t2.small"
        },
        {
            "worker_type": "license-server",
            "instance_type": "t2.small"
        },
        {
            "worker_type": "master",
            "instance_type": "t2.small"
        },
        {
            "worker_type": "deploy",
            "instance_type": "t2.small"
        },
        {
            "worker_type": "deployment-server",
            "instance_type": "t2.small"
        },
        {
            "worker_type": "monitoring-console",
            "instance_type": "t2.small"
        }
    ]
}
```

The best way to deploy configuration is to copy `EAF-Splunk\scripts\json_configurations\default_splunk_configuration.json` and tailor it to your needs.
