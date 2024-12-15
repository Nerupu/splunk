import json
import string

def is_valid_json(json_str):
    try:
        json.loads(json_str)
        return True
    except ValueError:
        return False

def check_key(dictionary: dict, key: str):
    if key in dictionary.keys():
        return dictionary[key]
    else:
        raise Exception(f"Key {key} is not found in dictionary")
    
def gentle_check_key(dictionary: dict, key: str):
    if key in dictionary.keys():
        return dictionary[key]
    else:
        return None

def get_common_parameters(commons_dict):
    return_dict = {}
    # common_name_part, vpc_id, subnet_id, security_group_ids, instance_profile, image, worker_type

    return_dict['instance_type'] = gentle_check_key(commons_dict, 'instance_type')
    return_dict['common_name_part'] = gentle_check_key(commons_dict, 'common_name_part')
    return_dict['ami_name'] = gentle_check_key(commons_dict, 'ami_name')
    return_dict['instance_profile'] = gentle_check_key(commons_dict, 'instance_profile')
    instance_profile = check_key(commons_dict, 'instance_profile')
    return_dict['instance_profile_name'] =  gentle_check_key(instance_profile, 'name')
    return_dict['subnet_az1'] = gentle_check_key(commons_dict, 'subnet_az1')
    return_dict['subnet_az2'] = gentle_check_key(commons_dict, 'subnet_az2')
    return_dict['subnet_az3'] = gentle_check_key(commons_dict, 'subnet_az3')
    return_dict['security_groups'] = gentle_check_key(commons_dict, 'security_groups')
    return_dict['worker_type'] = gentle_check_key(commons_dict, 'worker_type')
    return_dict['tags'] = gentle_check_key(commons_dict, 'tags')
    return_dict['root_volume'] = gentle_check_key(commons_dict, 'root_volume')
    return_dict['data_volumes'] = gentle_check_key(commons_dict, 'data_volumes')

    return return_dict

def get_from_dict_with_check(worker_dict: dict, default_dict: dict, key: str, optional: bool = False):
    if key in worker_dict.keys() and worker_dict[key] != '' and worker_dict[key] is not None:
        return worker_dict[key] 
    elif key in default_dict.keys() and default_dict[key] != '' and default_dict[key] is not None:
        return default_dict[key]
    else:
        raise Exception(f"Key {key} is not found in worker_specification and default_dict")

def tags_validation(tags_dict: dict):

    validation_file = "../workflow_parse/tag_validation.json"
    with open(validation_file) as f:
        content = f.read()
        validation_json = json.loads(content)['tags']

    # Validate if all required tags are present
    for required_key in validation_json['required']:
        if required_key not in tags_dict.keys():
            raise Exception(f"Key {required_key} is required in tags")
    
    # Validate if all required tags contain allowed values
    for required_key in validation_json['required']:
        used_value = tags_dict[required_key]
        allowed_values = validation_json['allowed_values'][required_key]
        if used_value not in allowed_values:
            raise Exception(f"Value {used_value} is not allowed for tag {required_key}. Allowed values are: {allowed_values}")


def get_tags(worker_dict: dict, default_dict: dict):
    tags = get_from_dict_with_check(worker_dict, default_dict, 'tags')
    required_tags = check_key(tags, 'required')
    optional_tags = gentle_check_key(tags, 'optional')
    
    tags_validation(required_tags)

    tags_merged = required_tags | {} if optional_tags is None else optional_tags

    return tags_merged

def generate_disk_names(data_volumes_quantity: int):
    disk_names = []
    device_letters = string.ascii_lowercase[5:16] #f-p

    if data_volumes_quantity > len(device_letters):
        raise ValueError(f"Too many disks, must be less than {len(device_letters)}")

    for index in range(data_volumes_quantity):
        # Generate a unique disk name
        disk_letter = device_letters[index]
        disk_name = f"/dev/sd{disk_letter}"


        disk_names.append(disk_name)

    return disk_names

def validate_mount_points(data_volumes: list):
    # Check if mount points are provided
    for volume in data_volumes:
        if 'mount_point' not in volume.keys():
            raise ValueError("Mount point must be provided for each disk")

    # Check if mount points are unique
    mount_points = [volume['mount_point'] for volume in data_volumes]
    if len(mount_points) != len(set(mount_points)):
        raise ValueError("Mount points must be unique")
    
    # Check if mount points are valid
    for mount_point in mount_points:
        if not mount_point.startswith('/'):
            raise ValueError(f"Mount point {mount_point} must start with /")
        if mount_point.endswith('/'):
            raise ValueError(f"Mount point {mount_point} must not end with /")
    
    return True

def manage_volumes(worker_specification: dict, common_parameters: dict, worker_dict: dict) -> dict:

    worker_dict['root_volume'] = get_from_dict_with_check(worker_specification, common_parameters, 'root_volume')
    data_volumes = get_from_dict_with_check(worker_specification, common_parameters, 'data_volumes')

    try:
        if worker_dict['root_volume']['volume_size'] is None:
            raise Exception("root volume size must be provided")
        if worker_dict['root_volume']['volume_type'] is None:
            raise Exception("root volume type must be provided")
        if worker_dict['root_volume']['delete_on_termination'] is None:
            raise Exception("root volume delete_on_termination must be provided")
    except Exception as e:
        raise Exception(f"Error in root volume: {worker_dict['root_volume']} | ERROR: {e}")

    for data_volume in data_volumes:
        try:
            volume_size = gentle_check_key(data_volume, 'volume_size')
            volume_type = gentle_check_key(data_volume, 'volume_type')
            delete_on_termination = gentle_check_key(data_volume, 'delete_on_termination')
            mount_point = gentle_check_key(data_volume, 'mount_point')
            iops = gentle_check_key(data_volume, 'iops')
            throughput = gentle_check_key(data_volume, 'throughput')
            if volume_size is None:
                raise Exception("volume size must be provided")
            if volume_type is None:
                raise Exception("volume type must be provided")
            if delete_on_termination is None:
                raise Exception("volume delete_on_termination must be provided")
            if mount_point is None:
                raise Exception("volume mount_point must be provided")
            if iops is None:
                raise Exception("volume iops must be provided")
            if throughput is None:
                raise Exception("volume throughput must be provided")
        except Exception as e:
            raise Exception(f"Error in data volume: {data_volume} | ERROR: {e}")

    worker_dict['data_volumes'] = {}
    if len(data_volumes) > 0:
        validate_mount_points(data_volumes)
        disk_quantity = len(data_volumes)
        device_names = generate_disk_names(disk_quantity)
        for volume in data_volumes:
            device_name = device_names.pop(0)
            worker_dict['data_volumes'][device_name] = volume
    

    return worker_dict

def create_vm_name(worker_dict, aws_region, vm_types_count):    

    vm_worker_type:str = check_key(worker_dict, 'vm_worker_type')
    required_tags = check_key(worker_dict, 'vm_tags')
    
    environment = check_key(required_tags, 'environment')
    product_name = check_key(required_tags, 'product')


    region = aws_region[:2]
    project_code = 'waa-eaf'
    product = product_name[:1]
    env = environment[:1]

    if "-" in vm_worker_type:
        type_code = ''.join(map(lambda x: x[:1], vm_worker_type.split('-')))
    else:
        type_code = vm_worker_type[:2]
    
    vm_types_count[vm_worker_type] += 1

    final_name = region + project_code + product + type_code + env + str(vm_types_count[vm_worker_type]).zfill(2)
    return final_name

def create_lb_names(general_dict):    

    required_tags = check_key(general_dict["load_balancer"], 'tags')
    
    environment = check_key(required_tags, 'environment')
    product_name = check_key(required_tags, 'product')

    region = general_dict["aws_region"][:2]
    project_code = 'waa-eaf'

    lb_names = {
        "alb_name" : f"{project_code}-{environment}-{region}-{product_name}-alb",
        "nlb_name" : f"{project_code}-{environment}-{region}-{product_name}-nlb"
    }

    return lb_names

def get_worker_type(worker_specification: dict, common_parameters: dict) -> str:
    vm_worker_type = get_from_dict_with_check(worker_specification, common_parameters, 'worker_type')
    suported_types = ["master", "indexer", "forwarder", "search-head", "license-server", "deploy", "deployment-server", "monitoring-console"]
    if vm_worker_type not in suported_types:
        raise Exception(f"Worker type {vm_worker_type} is not supported. Supported types are: {', '.join(suported_types)}")
    
    return vm_worker_type


class SubnetDispenser:

    def __init__(self, subnets:list, all_worker_types:list):
        self.subents_per_worker_type = {}
        self.iterator_per_worker_type = {}
        self.subnets_quantity = len(subnets)
        for worker_type in all_worker_types:
            self.subents_per_worker_type[worker_type] = subnets
            self.iterator_per_worker_type[worker_type] = 0


    def next(self, worker_type:str) -> str:
        subnet = self.subents_per_worker_type[worker_type][self.iterator_per_worker_type[worker_type]%self.subnets_quantity]
        self.iterator_per_worker_type[worker_type] += 1
        return subnet
    
def get_security_groups(worker_type, sg_mapping):
    type_to_key = {
        'master': 'master_cluster_node_sg_id',
        'indexer': 'indexer_sg_id',
        'forwarder': 'heavy_forwarder_sg_id',
        'search-head': 'search_head_sg_id',
        'license-server': 'license_server_sg_id',
        'deploy': 'deploy_sg_id',
        'deployment-server': 'deployment_server_sg_id',
        'monitoring-console': 'indexer_sg_id'
    }
    return [sg_mapping[type_to_key[worker_type]]]
