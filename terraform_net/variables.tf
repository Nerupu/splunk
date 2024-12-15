variable "use_ipam_pool" {
  description = "Determines whether IPAM pool is used for CIDR allocation"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to set on the resources"
  type        = map(string)
  default     = {}
}

variable "prefix" {}

variable "private_subnet_tags" {
  description = "Additional tags to be applied to private subnets"
  type        = map(string)
  default     = {}
}

variable "intra_subnet_tags" {
  description = "Additional tags to be applied to intra subnets"
  type        = map(string)
  default     = {}
}

variable "public_subnet_tags" {
  description = "Additional tags to be applied to public subnets"
  type        = map(string)
  default     = {}
}

variable "sg_tags" {
  description = "Additional tags to be applied to security"
  type        = map(string)
  default     = {}
}

variable "ssm_policy" {
  description = "List of SSM Iam policies"
  type        = list(string)
  default     = []
}

variable "privt_netmask" {
  description = "privt_netmask"
  type        = number
}

variable "other_netmask" {
  description = "other_netmask"
  type        = number
}

variable "private_num" {
  description = "Number of private subnets"
  type        = number
}

variable "public_num" {
  description = "Number of public subnets"
  type        = number
}

variable "intra_num" {
  description = "intra_num"
  type        = number
}

variable "azs_list" {
  description = "List of SSM Iam policies"
  type        = list(string)
  default     = []
}

variable "product" {
  description = "Name of the product"
  type        = string
  default     = "splunk"
}

variable "env" {
  description = "Environment"
  type        = string
}

variable "domain" {
  description = "Private DomainName"
  type        = string
  default     = "eafcore.com"
}
