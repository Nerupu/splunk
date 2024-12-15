resource "aws_iam_role" "this" {
  name               = "eaf-instance-ssm-${local.suffix}-role"
  assume_role_policy = file("${path.module}/policies/assumerole.json")

  tags = merge({ "Name" = "eaf-instance-ssm-${local.suffix}-role" }, { "owner" = "product-team" } ,var.tags)
}

resource "aws_iam_role_policy_attachment" "managed_policies" {
  for_each   = toset(var.ssm_policy)
  role       = aws_iam_role.this.name
  policy_arn = each.value
}

## Have to enable in EAF
resource "aws_iam_role_policy_attachment" "kms_policy" {
  role       = aws_iam_role.this.name
  policy_arn = data.aws_iam_policy.kmspolicy.arn
}

resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.this.name
  policy_arn = data.aws_iam_policy.session-manager-encrypted-connect.arn
}

resource "aws_iam_instance_profile" "this" {
  name = "eaf-instance-ssm-${local.suffix}-role"
  role = aws_iam_role.this.name
  tags = merge({ "owner" = "product-team" } ,var.tags)
} 