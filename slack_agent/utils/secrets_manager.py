import os
import json
import boto3
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SecretsManager:
    def __init__(self):
        self.client = boto3.client('secretsmanager')
    
    def get_secret_value_by_name(self, secret_name: str) -> Optional[str]:
        """
        Retrieve a secret value from AWS Secrets Manager by name
        """
        try:
            logger.debug(f"Retrieving secret: {secret_name}")
            response = self.client.get_secret_value(SecretId=secret_name)
            
            # Parse the secret string
            secret_dict = json.loads(response['SecretString'])
            
            # Handle different secret structures
            if 'api_key' in secret_dict:
                return secret_dict['api_key']
            elif len(secret_dict) == 1:
                # If there's only one key, return its value
                return list(secret_dict.values())[0]
            else:
                logger.error(f"Unexpected secret structure for {secret_name}: {list(secret_dict.keys())}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving secret {secret_name}: {e}")
            return None
    
    def get_anthropic_api_key(self) -> Optional[str]:
        """Get Anthropic API Key from Secrets Manager"""
        secret_name = os.environ.get('ANTHROPIC_API_KEY_SECRET_NAME')
        if not secret_name:
            logger.error("ANTHROPIC_API_KEY_SECRET_NAME environment variable not set")
            return None
        return self.get_secret_value_by_name(secret_name)

# Global instance for easy access
secrets_manager = SecretsManager()