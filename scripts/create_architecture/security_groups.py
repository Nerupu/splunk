from cloudformation import Resource
from logging_config import logger as l

def create_security_group(security_group_name:str, vpc:Resource, security_group_description:str):
    sg = Resource(security_group_name, "AWS::EC2::SecurityGroup")
    sg.add_property("VpcId", vpc.reference_this_resource())
    sg.add_property("GroupName", security_group_name)
    sg.add_property("GroupDescription", security_group_description)
    sg.add_property("SecurityGroupIngress", [])
    sg.add_property("SecurityGroupEgress", [])
    return sg

def create_security_group_ingress(trafic_source_security_group:Resource, security_group:Resource, port:str, protocol:str):
    ingress = Resource(f"{security_group.logical_id}Ingress{port.replace('-','')}{trafic_source_security_group.logical_id}", "AWS::EC2::SecurityGroupIngress")
    ingress.add_property("GroupId", security_group.reference_this_resource())
    ingress.add_property("SourceSecurityGroupId", trafic_source_security_group.reference_this_resource())
    ingress.add_property("IpProtocol", protocol)
    ingress.add_property("Description", f"Allow trafic from {trafic_source_security_group.logical_id} to {security_group.logical_id} on port {port} via protocol {protocol}")
    
    if '-' in port:
        port_from = port.split('-')[0]
        port_to = port.split('-')[1]
    else:
        port_from = port
        port_to = port

    ingress.add_property("FromPort", port_from)
    ingress.add_property("ToPort", port_to)
    return ingress

def manage_security_groups(sg_csv_file_path:str, vpc:Resource) -> tuple[list[Resource], list[dict]]:
    with open(sg_csv_file_path, "r") as f:
        rules_csv = f.readlines()
        for i, row in enumerate(rules_csv):
            rules_csv[i] = row.strip().replace(" ", "").split(",")

    # for row in rules_csv:
    #     l.info(row)

    all_sg = set()
    sg_rules:list[dict] = []
    for row in rules_csv[1:]:
        if len(row) != 4:
            l.info("WARNING: One of the rows in security_groups_rules.csv does not have 4 columns")
            continue
        source_sg, destination_sg, port, protocol = row[0], row[1], row[2], row[3]
        all_sg.add(source_sg)
        all_sg.add(destination_sg)
        sg_rules.append({
            "SourceSecurityGroupId": source_sg,
            "DestinationSecurityGroupId": destination_sg,
            "IpProtocol": protocol,
            "Port": port,
        })


    sg_resources = [
            create_security_group(
                security_group_name=sg,
                security_group_description=f"Security group for {sg} worker instances",
                vpc=vpc,
            ) for sg in all_sg
        ]

    def get_sg_resource_by_name(sg_name:str, sg_resources:list[Resource]):
        for sg in sg_resources:
            if sg.logical_id == sg_name:
                return sg
        return None


    sg_rules_resources = [
            create_security_group_ingress(
                trafic_source_security_group=get_sg_resource_by_name(rule["SourceSecurityGroupId"], sg_resources),
                security_group=get_sg_resource_by_name(rule["DestinationSecurityGroupId"], sg_resources),
                port=rule["Port"],
                protocol=rule["IpProtocol"],
            ) for rule in sg_rules
        ]

    # Allow all trafic from the same security group
    for sg in sg_resources:
        sg_rules_resources.append(
            create_security_group_ingress(
                trafic_source_security_group=sg,
                security_group=sg,
                port="1-65535",
                protocol="-1",
            )
        )
        
    return sg_resources, sg_rules_resources, all_sg