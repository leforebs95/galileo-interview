import json
import logging
import traceback
from typing import Dict, Any

# Set up logging first
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Initialize configuration once during cold start
logger.info("Initializing slack agent...")
try:
    logger.info("Importing config...")
    import config
    logger.info("Setting up Anthropic API key...")
    config.setup_anthropic_api_key()
    logger.info("Anthropic API key setup completed")
    
    logger.info("Importing agent graph...")
    from agent.graph import slack_agent
    logger.info("Agent imported successfully")
    
    # Flag to indicate successful initialization
    AGENT_INITIALIZED = True
    INITIALIZATION_ERROR = None
    
except Exception as e:
    logger.error(f"Failed to initialize agent: {e}")
    logger.error(f"Initialization traceback: {traceback.format_exc()}")
    AGENT_INITIALIZED = False
    INITIALIZATION_ERROR = str(e)
    slack_agent = None

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function for the Slack Agent
    """
    try:
        logger.info("Lambda handler starting...")
        
        # Check if initialization was successful
        if not AGENT_INITIALIZED:
            logger.error(f"Agent not initialized: {INITIALIZATION_ERROR}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Agent initialization failed: {INITIALIZATION_ERROR}'})
            }
        
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Handle API Gateway events
        if 'httpMethod' in event:
            return handle_api_gateway_event(event, context)
        
        # Handle direct invocation
        return handle_direct_invocation(event, context)
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }

def handle_api_gateway_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle API Gateway HTTP events
    """
    try:
        logger.info(f"Processing API Gateway event. Method: {event.get('httpMethod')}, Path: {event.get('path')}")
        
        # Handle health check
        if event.get('httpMethod') == 'GET' and event.get('path', '').endswith('/health'):
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'healthy', 
                    'service': 'slack-agent',
                    'version': '1.0.0',
                    'timestamp': __import__('datetime').datetime.utcnow().isoformat()
                })
            }
        
        # Handle POST requests to /invoke
        if event.get('httpMethod') == 'POST':
            logger.info("Processing POST request")
            
            body_str = event.get('body', '{}')
            logger.info(f"Request body: {body_str}")
            
            try:
                body = json.loads(body_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': f'Invalid JSON: {str(e)}'})
                }
            
            message = body.get('message', '')
            logger.info(f"Extracted message: {message}")
            
            if not message:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Message is required'})
                }
            
            logger.info("About to process message with agent...")
            response = process_message_with_agent(message)
            logger.info(f"Agent response: {response}")
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'response': response})
            }
        
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
        
    except Exception as e:
        logger.error(f"Error handling API Gateway event: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'API Gateway handler error: {str(e)}'})
        }

def handle_direct_invocation(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle direct Lambda invocation
    """
    try:
        logger.info("Processing direct invocation")
        message = event.get('message', '')
        if not message:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Message is required'})
            }
        
        response = process_message_with_agent(message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'response': response})
        }
        
    except Exception as e:
        logger.error(f"Error handling direct invocation: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Direct invocation error: {str(e)}'})
        }

def process_message_with_agent(message: str) -> str:
    """
    Process a message using the Slack agent
    """
    try:
        logger.info(f"Processing message: {message}")
        
        # Initialize the agent state
        initial_state = {
            "slack_message": message,
            "messages": [],
            "message_classification": None
        }
        
        logger.info("Invoking slack_agent...")
        # Run the agent
        result = slack_agent.invoke(initial_state)
        logger.info(f"Agent result: {result}")
        
        # Extract the response from the agent
        final_messages = result.get("messages", [])
        if final_messages and hasattr(final_messages[-1], 'content'):
            response = final_messages[-1].content
            logger.info(f"Extracted response: {response}")
            return response
        
        logger.warning("No valid response found in agent result")
        return "I processed your message successfully, but couldn't generate a response."
        
    except Exception as e:
        logger.error(f"Error processing message with agent: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return f"Sorry, I encountered an error processing your message: {str(e)}"

def main():
    """
    Local testing function
    """
    test_event = {
        'httpMethod': 'POST',
        'path': '/invoke',
        'body': json.dumps({'message': 'How do I use the search API?'})
    }
    
    result = lambda_handler(test_event, None)
    print(f"Result: {result}")

if __name__ == "__main__":
    main()