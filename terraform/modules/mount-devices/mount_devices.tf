resource "null_resource" "mount_volumes" {
    provisioner "local-exec" {
        command = <<-EOF
        echo "Wait for the SSM agent to be 'Online'..."
        while ! aws ssm describe-instance-information \
            --instance-information-filter-list "key=InstanceIds,valueSet=${var.instance_id}" \
            --query "InstanceInformationList[0].PingStatus" \
            --output text | grep -q '^Online$'; do
            echo "SSM agent not online yet. Retrying in 20 seconds..."
            sleep 20s
        done

        echo "SSM agent is online!"
        echo "Waiting 30s for SSM agent to be fully responsive..."
        sleep 30s

        echo "Configure block devices..."
        for device in $(echo '${jsonencode(var.disks)}' | jq -r 'keys[]' | tr '\n' ' ' ); do
            mount_path=$(echo '${jsonencode(var.disks)}' | jq -r --arg device "$device" '.[$device].mount_point')
            mount_uuid=$(uuidgen)
            aws ssm send-command \
            --instance-ids ${var.instance_id} \
            --document-name "AWS-RunShellScript" \
            --comment "${var.instance_id}: $device" \
            --parameters commands="[
                \"mkfs.xfs -f -L $${mount_path:0:12} -m uuid=$mount_uuid $device\",
                \"mkdir -p $mount_path\",
                \"echo UUID=$mount_uuid $mount_path    xfs    defaults,noatime    0 2 >> /etc/fstab\",
                \"mount $mount_path\"
            ]" \
            --output text
        done

        echo "Create /swapfile..."
        aws ssm send-command \
            --instance-ids ${self.id} \
            --document-name "AWS-RunShellScript" \
            --comment "${self.id}: /swapfile" \
            --parameters commands="[
                \"dd if=/dev/zero of=/swapfile bs=1M count=4096 conv=fdatasync oflag=direct\",
                \"chmod 600 /swapfile\",
                \"mkswap -L swapfile /swapfile\",
                \"echo /swapfile   none   swap   sw   0   0 >> /etc/fstab\",
                \"swapon /swapfile\"
            ]" \
        --output text

        echo "Get block device sumarry..."
        aws ssm send-command \
            --instance-ids ${var.instance_id} \
            --document-name "AWS-RunShellScript" \
            --comment "${var.instance_id}: summary" \
            --parameters commands="[
                \"lsblk --output NAME,SIZE,FSTYPE,LABEL,UUID\",
                \"swapon -l\",
                \"cat /etc/fstab\"
            ]" \
            --output text
        EOF
        interpreter = ["bash", "-c"]
    }
}
