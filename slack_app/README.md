# Slack App

The main Slack application component that handles incoming Slack events and messages.

## Overview

This application uses the Slack Bolt framework to:

- Handle incoming Slack messages and events
- Process file uploads and shares
- Coordinate with the Slack agent for intelligent responses
- Manage AWS S3 file storage
- Interface with various LLM providers

## Key Components

- `app.py`: Main Slack Bolt application setup
- `main.py`: Lambda handler for AWS deployment
- `listeners/`: Event listeners for different Slack events
- `utils/`: Utility modules for LLM calling and secrets management

## Environment Variables

Required environment variables:

- `SLACK_BOT_TOKEN`: Slack bot token
- `SLACK_SIGNING_SECRET`: Slack app signing secret
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `S3_BUCKET_NAME`: S3 bucket for file storage
- `LANGGRAPH_API_URL`: LangGraph agent API endpoint

## Development

1. Install dependencies:
```bash
uv sync
```

2. Set up environment variables in `.env` file

3. Run locally:
```bash
uv run python main.py
```

## Deployment

This component is deployed as an AWS Lambda function. Use the deployment scripts in the parent directory.