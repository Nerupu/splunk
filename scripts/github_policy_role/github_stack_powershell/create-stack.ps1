[CmdletBinding()]
Param(
    [string]$stackName = "EAF-GITHUB-ROLE",
    [int]$maxRetries = 60,
    [int]$retryIntervalSeconds = 2
)

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$stackName = "$stackName-$timestamp"

Write-Host "Make sure following environment variables are set: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, AWS_DEFAULT_REGION"

# Check if aws env params are set
if ($env:AWS_ACCESS_KEY_ID -eq $null){
    Write-Host "AWS_ACCESS_KEY_ID is not set"
    exit 1
}
if ($env:AWS_SECRET_ACCESS_KEY -eq $null){
    Write-Host "AWS_SECRET_ACCESS_KEY is not set"
    exit 1
}
if ($env:AWS_SESSION_TOKEN -eq $null){
    Write-Host "AWS_SESSION_TOKEN is not set"
    exit 1
}
if ($env:AWS_DEFAULT_REGION -eq $null){
    Write-Host "AWS_DEFAULT_REGION is not set"
    exit 1
}


#configure aws cli using environment variables
Write-Host "Configuring aws cli using environment variables"
aws configure set aws_access_key_id $env:AWS_ACCESS_KEY_ID
aws configure set aws_secret_access_key $env:AWS_SECRET_ACCESS_KEY
aws configure set aws_session_token $env:AWS_SESSION_TOKEN
aws configure set region $Env:AWS_DEFAULT_REGION
Write-Host "Configuration done."
Write-Host "Checking caller identity"

$identity = aws sts get-caller-identity | ConvertFrom-Json
$accountId = $identity.Account
$userId = $identity.UserId
$ARN = $identity.Arn

Write-Host "Caller identity:"
Write-Host "Account ID: $accountId"
Write-Host "User ID: $userId"
Write-Host "ARN: $ARN"



Write-Host "Validating template"

aws cloudformation validate-template --template-body file://github_role.yaml

#throw error if template is not valid
if ($LASTEXITCODE -ne 0) {
    Write-Host "Template is not valid"
    exit 1
}

Write-Host "Creating stack"
Write-Host "Stack name: $stackName"

aws cloudformation create-stack `
    --stack-name $stackName `
    --template-body file://github_role.yaml `
    --capabilities CAPABILITY_IAM `
    --parameters `
        ParameterKey=Region,ParameterValue=$env:AWS_DEFAULT_REGION `
        ParameterKey=AccountId,ParameterValue=$accountId

$desiredStatus = "CREATE_COMPLETE"

Start-Sleep -Seconds 2

try {
    for ($i = 1; $i -le $maxRetries; $i++) {
        $stack = aws cloudformation describe-stacks --stack-name $stackName | ConvertFrom-Json
        $stackStatus = $stack.Stacks[0].StackStatus
        Write-Host "Stack status: $stackStatus"
        if ($stackStatus -eq $desiredStatus) {
            Write-Host "Stack $stackName has reached the desired status: $desiredStatus"
            break
        }
        Start-Sleep -Seconds $retryIntervalSeconds
    }
}
catch [System.Management.Automation.PipelineStoppedException] {
    Write-Host "Script interrupted by user. Exiting loop."
}
# CREATE_FAILED, ROLLBACK_COMPLETE
if ($stackStatus -ne $desiredStatus) {
    Write-Host "Stack $stackName has not reached the desired status: $desiredStatus"
}

if ($stackStatus -eq "CREATE_FAILED" -or $stackStatus -eq "ROLLBACK_COMPLETE") {
    # Delete the failed stack
    aws cloudformation delete-stack --stack-name $stackName

    # Wait for the stack to be deleted
    $deleteStackStatus = aws cloudformation describe-stacks --stack-name $stackName --query 'Stacks[0].StackStatus'
    while ($deleteStackStatus -ne "DELETE_COMPLETE") {
        Write-Host "Waiting for stack deletion to complete. Current status: $deleteStackStatus"
        Start-Sleep -Seconds 10
        $deleteStackStatus = aws cloudformation describe-stacks --stack-name $stackName --query 'Stacks[0].StackStatus'
    }

    Write-Host "Stack $stackName has been successfully deleted."
    exit 0
}



# Describe the stack and get the outputs
$stack = aws cloudformation describe-stacks --stack-name $stackName --query 'Stacks[0].Outputs' | ConvertFrom-Json

Write-Host "Stack $stackName has been successfully created."
Write-Host "Stack outputs:"
Write-Host ""

# Print the outputs
foreach ($output in $stack) {
    # Write-Host "Output Key: $($output.OutputKey)"
    Write-Host "Github Role ARN: $($output.OutputValue)"
}
