terraform {
  #required_version = "~> 1.3.4"
  required_providers {
    aws = ">= 5.0"
  }

  backend "s3" {}

}

provider "aws" {
  alias  = "ipam"
  region = "eu-central-1"
}