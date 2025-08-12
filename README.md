# Slack Bot

A Slack bot application built with Python that integrates with AWS services and LangGraph for intelligent conversation handling.

## Architecture

This project consists of three main components:

- **slack_app**: The main Slack application that handles incoming messages and events
- **slack_agent**: A LangGraph-based agent for intelligent response generation
- **infrastructure**: AWS CDK infrastructure code for deployment

## Prerequisites

Before deploying the Slack Bot, run the one-time account setup:

```bash
./scripts/setup-aws-account.sh
```

## Quick Start

1. Install dependencies:
```bash
cd slack-bot
uv sync
```

2. Configure environment variables (see individual component READMEs for details)

3. Deploy infrastructure:
```bash
cd infrastructure
uv run cdk deploy
```

4. Deploy the application:
```bash
./scripts/deploy.py
```

## Components

### Slack App
The main Slack application that processes incoming messages and coordinates with the agent.

### Slack Agent  
A LangGraph-based conversational agent that provides intelligent responses using various tools and integrations.

### Infrastructure
AWS CDK code for deploying the application to AWS Lambda and related services.

## Development

Each component has its own pyproject.toml and can be developed independently. See the README in each subdirectory for component-specific instructions.

## Deployment

Use the provided deployment scripts for both development and production environments:

```bash
./scripts/build-and-deploy.sh
```