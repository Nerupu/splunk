locals {

  sub_list = [for i, k in var.azs_list : module.ipam_vpc.private_subnets[i]]

}

resource "aws_ec2_transit_gateway_vpc_attachment" "this" {
  subnet_ids         = local.sub_list
  transit_gateway_id = data.aws_ec2_transit_gateway.tgws.id
  vpc_id             = module.ipam_vpc.vpc_id


  tags = merge({ "Name" = "eaf-vpc-twg-attach" }, var.tags)

  lifecycle {
    ignore_changes = [
      transit_gateway_default_route_table_association,
      transit_gateway_default_route_table_propagation,
      subnet_ids
    ]
  }

}

resource "aws_route" "public_tgw" {
  count                  = length(module.ipam_vpc.public_route_table_ids)
  route_table_id         = module.ipam_vpc.public_route_table_ids[count.index]
  destination_cidr_block = "0.0.0.0/0"
  transit_gateway_id     = data.aws_ec2_transit_gateway.tgws.id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.this]
}

resource "aws_route" "intra_tgw" {
  count                  = length(module.ipam_vpc.intra_route_table_ids)
  route_table_id         = module.ipam_vpc.intra_route_table_ids[count.index]
  destination_cidr_block = "0.0.0.0/0"
  transit_gateway_id     = data.aws_ec2_transit_gateway.tgws.id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.this]
}

resource "aws_route" "private_tgw" {
  count                  = length(module.ipam_vpc.private_route_table_ids)
  route_table_id         = module.ipam_vpc.private_route_table_ids[count.index]
  destination_cidr_block = "0.0.0.0/0"
  transit_gateway_id     = data.aws_ec2_transit_gateway.tgws.id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.this]
}