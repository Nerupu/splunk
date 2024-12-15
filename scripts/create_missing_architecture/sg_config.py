import boto3
import logging
import concurrent.futures

class Rule:
    def __init__(self, port:int, protocol:str):
        self.port = port
        self.protocol = protocol


class InboundRule(Rule):
    def __init__(self, configured_sg_id:str, allowed_sg_id:str, port:int, protocol:str):
        super().__init__(port, protocol)
        self.configured_sg_id = configured_sg_id
        self.allowed_sg_id = allowed_sg_id
        self.configured_sg_name = 'empty'

    def __str__(self):
        if self.description:
            return self.description
        return f"{self.allowed_sg_id} can access {self.configured_sg_id} on port {self.port} using protocol {self.protocol}"

    def _get_sg_name(sg_id):
        ec2_client = boto3.client('ec2')

        response = ec2_client.describe_security_groups(GroupIds=[sg_id])

        if 'SecurityGroups' in response and len(response['SecurityGroups']) > 0:
            security_group = response['SecurityGroups'][0]
            sg_name = security_group['GroupName']
            return sg_name
        else:
            return None

    def create_description(self, sg_role_to_id:map):
        reverse_mapping = {v: k.replace('_sg_id', '').upper().replace('_', ' ') for k, v in sg_role_to_id.items()}
        try:
            allowed_sg_role = reverse_mapping[self.allowed_sg_id]
        except KeyError as ke:
            allowed_sg_role = self.allowed_sg_id
        try:
            configured_sg_role = reverse_mapping[self.configured_sg_id]
        except KeyError as ke:
            if self.configured_sg_name != 'empty' and self.configured_sg_name is not None:
                configured_sg_role = self.configured_sg_name
            elif self.configured_sg_name == 'empty':
                try:
                    configured_sg_role = self._get_sg_name(self.configured_sg_id)
                except Exception as e:
                    configured_sg_role = self.configured_sg_id
            else:
                configured_sg_role = self.configured_sg_id
                    

        port = self.port if str(self.port) != '-1' else 'all ports'
        port_str = f"port {port}" if str(self.port) != '-1' else 'all ports'

        protocol = self.protocol if self.protocol != '-1' else 'all protocols'
        protocol_str = f"protocol {protocol}" if self.protocol != '-1' else 'all protocols'
        self.description = f"Allow {allowed_sg_role} to access {configured_sg_role} on {port_str} using {protocol_str}"


def get_default_sg_id(vpc_id):
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_security_groups(
        Filters=[
            {'Name': 'group-name', 'Values': ['default']},
            {'Name': 'vpc-id', 'Values': [vpc_id]}
        ]
    )
    try:
        sg_id = response['SecurityGroups'][0]['GroupId']
    except IndexError:
        print("Default security group not found")
        sg_id = None
    return sg_id

def configure_inbound_and_outbound_rules(vpc_id:str, sg_role_to_id:map, access_to_load_balancer_sg_id:str, l:logging.Logger, jumphost_sg_id:str = None):
    l.info("Configuring inbound and outbound rules")
    l.info("")

    application_load_balancer_sg_id = sg_role_to_id['application_load_balancer_sg_id']
    search_head_sg_id = sg_role_to_id['search_head_sg_id']
    heavy_forwarder_sg_id = sg_role_to_id['heavy_forwarder_sg_id']
    deploy_sg_id = sg_role_to_id['deploy_sg_id']
    indexer_sg_id = sg_role_to_id['indexer_sg_id']
    deployment_server_sg_id = sg_role_to_id['deployment_server_sg_id']
    master_cluster_node_sg_id = sg_role_to_id['master_cluster_node_sg_id']
    license_server_sg_id = sg_role_to_id['license_server_sg_id']

    
    if access_to_load_balancer_sg_id:
        l.info(f"Provided security group that will have access to load balancer: {access_to_load_balancer_sg_id}")
    else:
        l.info("No additional security group provided, using default one")
        access_to_load_balancer_sg_id = get_default_sg_id(vpc_id)
        if not access_to_load_balancer_sg_id:
            l.warning("No default security group found")






    # Create inbound rules
    inbound_rules = [
        InboundRule(application_load_balancer_sg_id, access_to_load_balancer_sg_id, 443, 'tcp'), 
        InboundRule(application_load_balancer_sg_id, access_to_load_balancer_sg_id, 80, 'tcp'), 
        InboundRule(application_load_balancer_sg_id, access_to_load_balancer_sg_id, 8000, 'tcp'), 

        InboundRule(search_head_sg_id, application_load_balancer_sg_id, 8000, 'tcp'), 
        InboundRule(search_head_sg_id, deploy_sg_id, 8089, 'tcp'), 
        InboundRule(search_head_sg_id, deploy_sg_id, 8191, 'tcp'), 
        InboundRule(search_head_sg_id, indexer_sg_id, 8089, 'tcp'), 

        InboundRule(deploy_sg_id, search_head_sg_id, 8089, 'tcp'),
        InboundRule(deploy_sg_id, search_head_sg_id, 8191, 'tcp'), 

        InboundRule(indexer_sg_id, search_head_sg_id, 9997, 'tcp'), 
        InboundRule(indexer_sg_id, deploy_sg_id, 9997, 'tcp'), 
        InboundRule(indexer_sg_id, heavy_forwarder_sg_id, 9997, 'tcp'), 
        InboundRule(indexer_sg_id, master_cluster_node_sg_id, 8089, 'tcp'), 
        InboundRule(indexer_sg_id, master_cluster_node_sg_id, 9997, 'tcp'), 
        InboundRule(indexer_sg_id, license_server_sg_id, 9997, 'tcp'),

        #no inbound rules for heavy forwarder sg

        InboundRule(deployment_server_sg_id, heavy_forwarder_sg_id, 8089, 'tcp'), 

        InboundRule(master_cluster_node_sg_id, heavy_forwarder_sg_id, 8089, 'tcp'), 
        InboundRule(master_cluster_node_sg_id, indexer_sg_id, 8089, 'tcp'), 

        InboundRule(license_server_sg_id, master_cluster_node_sg_id, 8089, 'tcp'), 
        InboundRule(license_server_sg_id, deployment_server_sg_id, 8089, 'tcp'), 
        InboundRule(license_server_sg_id, deploy_sg_id, 8089, 'tcp'), 
        InboundRule(license_server_sg_id, search_head_sg_id, 8089, 'tcp'), 

        InboundRule(search_head_sg_id, license_server_sg_id, 8089, 'tcp'), 

        InboundRule(indexer_sg_id, search_head_sg_id, 8089, 'tcp'), 

        InboundRule(deployment_server_sg_id, heavy_forwarder_sg_id, 9997, 'tcp'), 

        InboundRule(master_cluster_node_sg_id, search_head_sg_id, 8089, 'tcp'), 

        InboundRule(license_server_sg_id, indexer_sg_id, 8089, 'tcp'), 
        InboundRule(license_server_sg_id, heavy_forwarder_sg_id, 8089, 'tcp'), 

    ]

    port_for_jumphost = 8000
    jumphost_rules = [
        InboundRule(application_load_balancer_sg_id, jumphost_sg_id, port_for_jumphost, 'tcp'),
        InboundRule(search_head_sg_id              , jumphost_sg_id, port_for_jumphost, 'tcp'),
        InboundRule(deploy_sg_id                   , jumphost_sg_id, port_for_jumphost, 'tcp'),
        InboundRule(indexer_sg_id                  , jumphost_sg_id, port_for_jumphost, 'tcp'),
        InboundRule(deployment_server_sg_id        , jumphost_sg_id, port_for_jumphost, 'tcp'),
        InboundRule(master_cluster_node_sg_id      , jumphost_sg_id, port_for_jumphost, 'tcp'),
        InboundRule(license_server_sg_id           , jumphost_sg_id, port_for_jumphost, 'tcp'),
    ]

    if jumphost_sg_id:
        inbound_rules.extend(jumphost_rules)

    for sg_id in [
        application_load_balancer_sg_id,
        search_head_sg_id,
        heavy_forwarder_sg_id,
        deploy_sg_id,
        indexer_sg_id,
        deployment_server_sg_id,
        master_cluster_node_sg_id,
        license_server_sg_id
    ]:
        inbound_rules.append(
            InboundRule(sg_id, sg_id, -1, '-1')
        )


    l.info('Following inbound rules will be created:')
    for rule in inbound_rules:
        rule.create_description(sg_role_to_id=sg_role_to_id)
        l.info(rule)
    
    l.info('')

    number_of_conncurrent_workers = 12
    l.info(f"Creating rules using {number_of_conncurrent_workers} workers...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=number_of_conncurrent_workers) as executor:
        futures = []
        
        for rule in inbound_rules:
            future = executor.submit(add_inbound_rule, vpc_id, rule)
            futures.append(future)
        
        concurrent.futures.wait(futures)
        
    
    l.info('Creation completed')
    l.info('')





def add_inbound_rule(vpc_id:str, rule:InboundRule):
    assert vpc_id is not None
    assert rule is not None
    assert isinstance(rule, InboundRule)

    if rule.allowed_sg_id is None or rule.configured_sg_id is None:
        return
    
    if rule.port == -1:
        start_port = 0
        end_port = 65535
    else:
        start_port = rule.port
        end_port = rule.port

    ec2 = boto3.client('ec2')
    response = ec2.authorize_security_group_ingress(
        GroupId=rule.configured_sg_id,
        IpPermissions=[
            {
                'IpProtocol': rule.protocol,
                'FromPort': start_port,
                'ToPort': end_port,
                'UserIdGroupPairs': [
                    {
                        'GroupId': rule.allowed_sg_id,
                        'Description': rule.description,
                        'VpcId': vpc_id
                    }
                ]
            }
        ]
    )