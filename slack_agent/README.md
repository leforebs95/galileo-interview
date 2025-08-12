# Slack Agent

A LangGraph-based conversational agent that provides intelligent responses for the Slack bot.

## Overview

This agent uses LangGraph to create a stateful conversation flow with:

- Multiple tool integrations
- State management across conversation turns
- Intelligent routing between different response strategies
- Support for various LLM providers

## Architecture

- `agent/`: Core agent implementation
  - `graph.py`: LangGraph workflow definition
  - `state.py`: Conversation state management
  - `tools.py`: Available tools and integrations
  - `types.py`: Type definitions
- `main.py`: FastAPI server for the agent
- `langgraph.json`: LangGraph configuration

## Key Features

- Stateful conversation handling
- Tool calling capabilities
- Multi-turn dialogue support
- Integration with external APIs and services

## Environment Variables

Required environment variables:

- `ANTHROPIC_API_KEY`: Anthropic API key
- `OPENAI_API_KEY`: OpenAI API key
- Additional tool-specific API keys as needed

## Development

1. Install dependencies:
```bash
uv sync
```

2. Set up environment variables

3. Run the LangGraph server:
```bash
uv run langgraph dev
```

4. Or run the FastAPI server directly:
```bash
uv run python main.py
```

## Deployment

This component is deployed as an AWS Lambda function with the LangGraph runtime. The deployment process is handled by the infrastructure stack.