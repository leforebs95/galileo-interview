from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    SecretValue,
    aws_lambda as _lambda,
    aws_ecr as ecr,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_logs as logs,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct
import os
import json
from dotenv import load_dotenv

load_dotenv()

class SlackAgentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment: str = "dev", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self._environment = environment
        
        # Reference existing ECR Repository
        self.ecr_repository = ecr.Repository.from_repository_name(
            self, "SlackAgentRepository",
            repository_name=f"puresort-slack-agent-{environment}"
        )
        
        # Get or create secrets
        self.secrets = self._get_or_create_secrets()
        
        # Lambda execution role with secrets access
        lambda_role = iam.Role(
            self, "SlackAgentLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "SecretsManagerAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "secretsmanager:GetSecretValue",
                            ],
                            resources=[f"{secret.secret_arn}*" for secret in self.secrets.values()]
                        )
                    ]
                )
            }
        )
        
        # Create log group for Lambda function
        log_group = logs.LogGroup(
            self, "SlackAgentLogGroup",
            log_group_name=f"/aws/lambda/puresort-slack-agent-{environment}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Lambda function using your preloaded ECR container image
        self.lambda_function = _lambda.DockerImageFunction(
            self, "SlackAgentFunction",
            function_name=f"puresort-slack-agent-{environment}",
            code=_lambda.DockerImageCode.from_ecr(
                repository=self.ecr_repository,
                tag="latest"
            ),
            role=lambda_role,
            timeout=Duration.seconds(300),
            memory_size=1024,
            environment={
                "ENVIRONMENT": environment.upper(),
                "LOG_LEVEL": "INFO" if environment == "prod" else "DEBUG",
                "ANTHROPIC_API_KEY_SECRET_NAME": f"{self._environment}/slack-agent/anthropic-api-key",
            },
            log_group=log_group,
        )
        
        # API Gateway for direct agent invocation
        self.api_gateway = apigw.RestApi(
            self, "SlackAgentApi",
            rest_api_name=f"puresort-slack-agent-{environment}",
            description="API Gateway for Slack Agent direct invocation",
            deploy_options=apigw.StageOptions(
                stage_name=environment,
                throttling_rate_limit=100,
                throttling_burst_limit=200,
                logging_level=apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=environment != "prod",
            ),
        )
        
        # Lambda integration with proxy enabled for easier handling
        lambda_integration = apigw.LambdaIntegration(
            self.lambda_function,
            proxy=True,  # This passes the full request to your Lambda
            integration_responses=[
                apigw.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
                        "method.response.header.Content-Type": "'application/json'"
                    }
                )
            ]
        )
        
        # Create /invoke endpoint for direct agent calls
        invoke_resource = self.api_gateway.root.add_resource("invoke")
        invoke_resource.add_method(
            "POST", 
            lambda_integration,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Content-Type": True
                    }
                )
            ]
        )
        
        # Add CORS support for web clients
        invoke_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"]
        )
        
        # Optional: Add a health check endpoint
        health_resource = self.api_gateway.root.add_resource("health")
        health_resource.add_method(
            "GET",
            lambda_integration,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Content-Type": True
                    }
                )
            ]
        )
        
        # Outputs
        CfnOutput(
            self, "ECRRepositoryURI",
            value=self.ecr_repository.repository_uri,
            description="ECR Repository URI for Docker images"
        )
        
        CfnOutput(
            self, "LambdaFunctionName",
            value=self.lambda_function.function_name,
            description="Lambda Function Name"
        )
        
        CfnOutput(
            self, "AgentInvokeUrl",
            value=f"{self.api_gateway.url}invoke",
            description="URL to invoke the agent directly"
        )
        
        CfnOutput(
            self, "AgentHealthUrl",
            value=f"{self.api_gateway.url}health",
            description="Health check endpoint"
        )
        
        CfnOutput(
            self, "ApiGatewayBaseUrl",
            value=self.api_gateway.url,
            description="Base API Gateway URL"
        )

        # Output secret ARNs for reference
        for secret_name, secret in self.secrets.items():
            CfnOutput(
                self, f"{secret_name.replace('_', '')}SecretArn",
                value=secret.secret_arn,
                description=f"Secret ARN for {secret_name}",
                export_name=f"{environment}-slack-agent-{secret_name.lower().replace('_', '-')}-secret-arn"
            )

    def _get_or_create_secrets(self) -> dict:
        """Get existing secrets or create new ones using conditional logic"""
        
        secrets_config = {
            "ANTHROPIC_API_KEY": "anthropic-api-key"
        }
        
        secrets = {}
        
        for env_var, secret_name in secrets_config.items():
            secrets[env_var] = self._get_or_create_secret(env_var, secret_name)
        
        return secrets
    
    def _secret_exists(self, secret_name: str) -> bool:
        """Check if a secret actually exists in AWS Secrets Manager"""
        try:
            print(f"Checking if secret exists: {secret_name}")
            import boto3
            secrets_client = boto3.client('secretsmanager')
            secrets_client.describe_secret(SecretId=secret_name)
            print(f"✓ Secret exists: {secret_name}")
            return True
        except Exception as e:
            if hasattr(e, 'response') and e.response.get('Error', {}).get('Code') == 'ResourceNotFoundException':
                print(f"✗ Secret not found: {secret_name}")
                return False
            else:
                print(f"Error checking secret existence for {secret_name}: {e}")
                # If we can't determine, assume it doesn't exist and try to create
                return False

    def _get_or_create_secret(self, env_var: str, secret_name: str) -> secretsmanager.Secret:
        """Get existing secret or create new one"""
        secret_full_name = f"{self._environment}/slack-agent/{secret_name}"
        if self._secret_exists(secret_full_name):
            # Secret exists, create reference
            return secretsmanager.Secret.from_secret_name_v2(
                self, f"Existing{env_var.replace('_', '').title()}Secret",
                secret_name=secret_full_name
            )
        else:
            # Secret doesn't exist, create it
            local_value = os.environ.get(env_var)
            if not local_value:
                raise ValueError(f"Environment variable {env_var} is required for creating new secret")
            
            return secretsmanager.Secret(
                self, f"SlackAgent{env_var.replace('_', '').title()}Secret",
                secret_name=secret_full_name,
                description=f"Slack Agent {secret_name.replace('-', ' ').title()} for {self._environment} environment",
                secret_string_value=SecretValue.unsafe_plain_text(
                    json.dumps({"value": local_value})
                ),
                removal_policy=RemovalPolicy.RETAIN
            )