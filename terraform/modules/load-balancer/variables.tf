variable "alb_config" {
  type = list(map(string))
}

variable "nlb_config" {
  type = list(map(string))
}

variable "alb_sgs" { 
  type = list(string)
}

variable "tags" { 
  type = map(string)
}

variable "names" { 
  type = map(string)
}

variable "cert_name" {
  type = string
}