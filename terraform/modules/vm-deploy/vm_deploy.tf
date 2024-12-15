resource "aws_instance" "splunk_vm" {

  ami                    = data.aws_ami.ami_id.id
  instance_type          = var.instance_type
  vpc_security_group_ids = data.aws_security_group.aws_sgs.*.id
  subnet_id              = var.subnet
  iam_instance_profile   = var.instance_profile
  metadata_options {
    http_endpoint          = "enabled"
    instance_metadata_tags = "enabled"
  }

  tags        = merge(var.tags, tomap({ "Name" = "${var.name}", "Type" = "${var.type_vm}" }))
  volume_tags = merge(var.tags, tomap({ "Name" = "${var.name}" }))

  root_block_device {
    volume_size           = var.root_volume_conf.volume_size
    volume_type           = var.root_volume_conf.volume_type
    delete_on_termination = var.root_volume_conf.delete_on_termination
  }
  dynamic "ebs_block_device" {
    for_each = length(var.data_volumes_conf) != 0 ? var.data_volumes_conf : {}
    content {
      device_name           = ebs_block_device.key
      volume_size           = ebs_block_device.value["volume_size"]
      volume_type           = ebs_block_device.value["volume_type"]
      iops                  = ebs_block_device.value["iops"]
      throughput            = ebs_block_device.value["throughput"]
      delete_on_termination = ebs_block_device.value["delete_on_termination"]
    }
  }
}