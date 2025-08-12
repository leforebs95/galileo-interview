from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_lambda as _lambda,
    aws_ecr as ecr,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_logs as logs,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

class SlackAgentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment: str = "dev", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
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
                                "secretsmanager:DescribeSecret"
                            ],
                            resources=[secret.secret_arn for secret in self.secrets.values()]
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
                "ANTHROPIC_API_KEY_SECRET_NAME": f"{environment}/slack-agent/anthropic-api-key",
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
    
    def _get_or_create_secret(self, env_var: str, secret_name: str):
        """Get existing secret or create placeholder - helper method"""
        full_secret_name = f"{self.environment}/{self.stack_name.lower().replace('stack', '').replace('slack', 'slack-')}/{secret_name}"
        
        try:
            # Try to import existing secret
            print(f"Attempting to reference existing secret: {full_secret_name}")
            secret = secretsmanager.Secret.from_secret_name_v2(
                self, f"{env_var}Secret",
                secret_name=full_secret_name
            )
            print(f"Successfully referenced existing secret: {full_secret_name}")
            return secret
            
        except Exception as e:
            # Create new secret if it doesn't exist
            print(f"Secret {full_secret_name} not found, creating placeholder. Error: {str(e)}")
            
            secret = secretsmanager.Secret(
                self, f"{env_var}Secret",
                secret_name=full_secret_name,
                description=f"{env_var} for Slack Agent",
                generate_secret_string=secretsmanager.SecretStringGenerator(
                    secret_string_template='{"api_key": ""}',
                    generate_string_key="api_key",
                    exclude_characters='" \\',
                ),
                removal_policy=RemovalPolicy.RETAIN  # Important: Don't delete secrets on stack deletion
            )
            
            print(f"Created new secret: {full_secret_name}")
            return secret