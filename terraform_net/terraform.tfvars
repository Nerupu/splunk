tags = {
  product   = "splunk"
  terraform = "true"
  project   = "EAF"
}

prefix = "eaf"


private_subnet_tags = {
  private  = "true"
  tier     = "tier1"
  resource = "subnet"
}

intra_subnet_tags = {
  private  = "true"
  tier     = "tier2"
  resource = "subnet"
}

public_subnet_tags = {
  private  = "false"
  tier     = "public"
  resource = "subnet"
}

sg_tags = {
  resource = "securitygroup"
}

ssm_policy = [
  "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
  "arn:aws:iam::aws:policy/AmazonSSMDirectoryServiceAccess",
  "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy",
  "arn:aws:iam::aws:policy/AmazonS3FullAccess"

]

privt_netmask = 2
other_netmask = 4
private_num   = 3
public_num    = 1
intra_num     = 3
azs_list      = ["a", "b", "c"]



