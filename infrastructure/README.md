# Infrastructure

AWS CDK infrastructure code for deploying the Slack Bot application.

## Overview

This module contains AWS CDK constructs and stacks for deploying:

- Lambda functions for the Slack app and agent
- IAM roles and policies
- API Gateway endpoints
- S3 buckets for file storage
- CloudWatch logs and monitoring

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. CDK CLI installed: `npm install -g aws-cdk`
3. Python dependencies installed: `uv sync`

## Deployment

Deploy to development environment:
```bash
uv run cdk deploy SlackBotDev SlackAgentDev
```

Deploy to production environment:
```bash
uv run cdk deploy SlackBotProd SlackAgentProd
```

## Configuration

Environment-specific configuration is managed through CDK context and environment variables. See the stack files for available configuration options.

## Stacks

- `SlackBotStack`: Infrastructure for the main Slack application
- `SlackAgentStack`: Infrastructure for the LangGraph agent service