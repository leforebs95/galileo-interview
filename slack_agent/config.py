import os
import logging
from dotenv import load_dotenv

# Try to import secrets manager (will fail in dev if boto3 not available)
try:
    from utils.secrets_manager import secrets_manager
    SECRETS_AVAILABLE = True
except ImportError:
    SECRETS_AVAILABLE = False
    secrets_manager = None

load_dotenv()

logger = logging.getLogger(__name__)

def setup_anthropic_api_key():
    """
    Set up Anthropic API key in environment variable for LangChain to use
    """
    # Check if already set
    if os.environ.get("ANTHROPIC_API_KEY"):
        logger.info("ANTHROPIC_API_KEY already set in environment")
        return
    
    environment = os.environ.get("ENVIRONMENT", "DEV").upper()
    
    if environment == "PROD" and SECRETS_AVAILABLE:
        # Production: Use AWS Secrets Manager
        logger.info("Retrieving Anthropic API key from AWS Secrets Manager")
        api_key = secrets_manager.get_anthropic_api_key()
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
            logger.info("Successfully set ANTHROPIC_API_KEY from Secrets Manager")
        else:
            raise ValueError("Failed to retrieve Anthropic API key from Secrets Manager")
    else:
        # Development: Should be set in environment variables or .env file
        logger.info("Using environment variables for Anthropic API key")
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Please set it in your .env file for development or ensure secrets are configured for production."
            )

# Initialize API key when module is imported
try:
    setup_anthropic_api_key()
    logger.info("Anthropic API key configuration completed successfully")
except Exception as e:
    logger.error(f"Failed to setup Anthropic API key: {e}")
    # Don't raise here to allow the module to import, but the error will surface when actually trying to use the API