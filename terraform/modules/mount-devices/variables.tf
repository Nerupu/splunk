variable "instance_id" {
  type = string
}

variable "disks" {
  type = map(map(string))
}