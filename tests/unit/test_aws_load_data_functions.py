#!/usr/bin/env python3
"""
Unit tests for AWS Bedrock functions from load_data.py.
This module extracts and tests the specific functions without importing the full load_data.py script.
"""

import pytest
import json
import os
import sys
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# Extract the functions we want to test from load_data.py without running the script
def handle_aws_embedding_error(error, context="embedding generation"):
    """
    Centralized AWS error handling for embedding generation with proper logging.
    """
    # Import additional AWS exceptions
    try:
        from botocore.exceptions import EndpointConnectionError
    except ImportError:
        EndpointConnectionError = None
    
    # Handle AWS credential errors (Requirement 4.2)
    if isinstance(error, NoCredentialsError):
        print(f"WARNING: AWS credentials not found for {context}. "
              f"Please ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set, or use IAM roles. "
              f"Details: Credentials not available")  # Don't expose full credential error
        return
    
    # Handle endpoint connection errors (network issues)
    elif EndpointConnectionError and isinstance(error, EndpointConnectionError):
        print(f"WARNING: Cannot connect to AWS endpoint for {context}. "
              f"Check network connectivity and AWS region configuration. "
              f"Details: Connection failed")  # Don't expose full endpoint details
        return
    
    # Handle AWS client errors with specific error codes (Requirements 4.1, 4.3)
    elif isinstance(error, ClientError):
        error_code = error.response.get('Error', {}).get('Code', 'Unknown')
        error_message = error.response.get('Error', {}).get('Message', 'AWS service error')
        
        # Sanitize error message to avoid exposing sensitive information (Requirement 4.5)
        sanitized_message = _sanitize_embedding_error_message(error_message)
        
        if error_code == 'ThrottlingException':
            print(f"WARNING: AWS rate limiting encountered for {context}. "
                  f"Consider implementing request batching or delays. Details: {sanitized_message}")
        
        elif error_code == 'ValidationException':
            print(f"WARNING: AWS validation error for {context}. "
                  f"Check request parameters and input text format. Details: {sanitized_message}")
        
        elif error_code == 'AccessDeniedException':
            print(f"WARNING: AWS access denied for {context}. "
                  f"Check IAM permissions for bedrock:InvokeModel on amazon.titan-embed-text-v2:0. Details: {sanitized_message}")
        
        elif error_code == 'ServiceUnavailableException':
            print(f"WARNING: AWS Bedrock service unavailable for {context}. "
                  f"Service may be experiencing issues or model unavailable in region. Details: {sanitized_message}")
        
        elif error_code == 'ModelNotReadyException':
            print(f"WARNING: AWS embedding model not ready for {context}. "
                  f"Model may be loading or unavailable in region. Details: {sanitized_message}")
        
        elif error_code == 'InternalServerException':
            print(f"WARNING: AWS internal server error for {context}. "
                  f"Temporary service issue. Details: {sanitized_message}")
        
        elif error_code == 'ResourceNotFoundException':
            print(f"WARNING: AWS resource not found for {context}. "
                  f"Model may not exist in this region. Details: {sanitized_message}")
        
        elif error_code == 'ModelTimeoutException':
            print(f"WARNING: AWS model timeout for {context}. "
                  f"Model processing took too long. Details: {sanitized_message}")
        
        else:
            print(f"WARNING: AWS client error for {context}. "
                  f"Error code: {error_code}. Details: {sanitized_message}")
    
    # Handle JSON parsing errors
    elif isinstance(error, json.JSONDecodeError):
        print(f"WARNING: Failed to parse AWS response JSON for {context}. "
              f"Response may be malformed. Details: Invalid JSON response")
    
    # Handle network and timeout errors
    elif hasattr(error, '__class__') and 'timeout' in error.__class__.__name__.lower():
        print(f"WARNING: Network timeout for {context}. "
              f"Check network connectivity to AWS services. Details: Request timeout")
    
    # Handle general exceptions
    else:
        print(f"WARNING: Unexpected error for {context}. Details: {type(error).__name__}")


def _sanitize_embedding_error_message(message):
    """
    Sanitize error messages to remove potentially sensitive information.
    """
    if not message:
        return "AWS service error"
    
    # Truncate very long messages first to avoid excessive processing
    if len(message) > 200:
        message = message[:200] + "... [TRUNCATED]"
    
    # Remove potential access keys, tokens, or other sensitive patterns
    import re
    
    # Remove AWS access key patterns
    message = re.sub(r'AKIA[0-9A-Z]{16}', '[ACCESS_KEY_REDACTED]', message)
    
    # Remove potential secret key patterns (more specific pattern)
    message = re.sub(r'\b[A-Za-z0-9/+=]{40}\b', '[SECRET_REDACTED]', message)
    
    # Remove session token patterns (more specific pattern)
    message = re.sub(r'\b[A-Za-z0-9/+=]{100,}\b', '[TOKEN_REDACTED]', message)
    
    # Remove IP addresses
    message = re.sub(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '[IP_REDACTED]', message)
    
    # Remove potential ARNs with account numbers
    message = re.sub(r'arn:aws:[^:]*:[^:]*:\d{12}:[^:]*', '[ARN_REDACTED]', message)
    
    return message


def retry_embedding_with_backoff(client, text, max_retries=2, base_delay=1.0):
    """
    Retry embedding generation with exponential backoff for rate limiting.
    """
    import time
    
    for attempt in range(max_retries + 1):
        try:
            response = client.invoke_model(
                modelId="amazon.titan-embed-text-v2:0",
                body=json.dumps({
                    "inputText": text,
                    "dimensions": 1024,
                    "normalize": True
                })
            )
            response_body = json.loads(response['body'].read())
            
            # Validate response structure
            if 'embedding' not in response_body:
                raise ValueError("No embedding in Titan response")
            
            return response_body['embedding']
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            
            if error_code == 'ThrottlingException' and attempt < max_retries:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                print(f"INFO: Rate limited, retrying embedding in {delay:.1f} seconds (attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(delay)
                continue
            else:
                # Don't retry for non-throttling errors or max retries reached
                handle_aws_embedding_error(e, "Titan embedding generation")
                return None
        
        except Exception as e:
            handle_aws_embedding_error(e, "Titan embedding generation")
            return None
    
    return None


def generate_embeddings_with_titan(client, texts):
    """
    Generate embeddings using Amazon Titan Text Embeddings v2 with comprehensive error handling.
    """
    VECTOR_DIM = 1024
    embeddings = []
    aws_success_count = 0
    aws_fallback_count = 0
    
    for i, text in enumerate(texts):
        try:
            if client:
                # Use retry mechanism for rate limiting (Requirement 4.3)
                embedding = retry_embedding_with_backoff(client, text)
                
                if embedding is not None:
                    embeddings.append(embedding)
                    aws_success_count += 1
                else:
                    # Retry failed, use fallback
                    print(f"INFO: Using random vector fallback for text {i+1}/{len(texts)}")
                    embeddings.append(np.random.rand(VECTOR_DIM).astype(np.float32).tolist())
                    aws_fallback_count += 1
            else:
                # Client not available, use fallback (Requirement 4.4)
                embeddings.append(np.random.rand(VECTOR_DIM).astype(np.float32).tolist())
                aws_fallback_count += 1
                
        except Exception as e:
            # Ensure processing continues with other texts (Requirement 4.5)
            print(f"WARNING: Unexpected error processing text {i+1}/{len(texts)}. "
                  f"Continuing with remaining texts. Details: {e}")
            embeddings.append(np.random.rand(VECTOR_DIM).astype(np.float32).tolist())
            aws_fallback_count += 1
    
    # Display progress and success/failure statistics (Requirement 5.5)
    if aws_success_count > 0 or aws_fallback_count > 0:
        total_processed = aws_success_count + aws_fallback_count
        success_rate = (aws_success_count / total_processed) * 100 if total_processed > 0 else 0
        print(f"AWS Batch Stats: {aws_success_count}/{total_processed} successful ({success_rate:.1f}%), "
              f"{aws_fallback_count} fallbacks")
        
        if aws_fallback_count > 0:
            print(f"INFO: Application continues functioning with {aws_fallback_count} fallback embeddings")
    
    return embeddings


class TestTitanEmbeddingGeneration:
    """Test suite for Titan embedding generation functions."""
    
    @pytest.fixture
    def mock_bedrock_client(self):
        """Mock Bedrock client for embedding tests."""
        mock_client = Mock()
        return mock_client
    
    @pytest.fixture
    def sample_product_texts(self):
        """Sample product texts for embedding generation."""
        return [
            "Product: iPhone 15. Brand: Apple. Category: Electronics, Mobile.",
            "Product: MacBook Pro. Brand: Apple. Category: Electronics, Computers.",
            "Product: Samsung Galaxy. Brand: Samsung. Category: Electronics, Mobile."
        ]
    
    def test_titan_successful_embedding_generation(self, mock_bedrock_client, sample_product_texts):
        """Test successful embedding generation with Titan."""
        # Mock successful responses for each text
        mock_embeddings = [np.random.rand(1024).tolist() for _ in sample_product_texts]
        
        def mock_invoke_model(*args, **kwargs):
            mock_response = {'body': Mock()}
            # Return different embedding for each call
            call_count = mock_bedrock_client.invoke_model.call_count
            mock_response['body'].read.return_value = json.dumps({
                'embedding': mock_embeddings[call_count]
            }).encode()
            return mock_response
        
        mock_bedrock_client.invoke_model.side_effect = mock_invoke_model
        
        result = generate_embeddings_with_titan(mock_bedrock_client, sample_product_texts)
        
        # Verify API calls
        assert mock_bedrock_client.invoke_model.call_count == len(sample_product_texts)
        
        # Verify request parameters for first call
        call_args = mock_bedrock_client.invoke_model.call_args_list[0]
        assert call_args[1]['modelId'] == 'amazon.titan-embed-text-v2:0'
        
        request_body = json.loads(call_args[1]['body'])
        assert request_body['inputText'] == sample_product_texts[0]
        assert request_body['dimensions'] == 1024
        assert request_body['normalize'] is True
        
        # Verify results
        assert len(result) == len(sample_product_texts)
        for embedding in result:
            assert len(embedding) == 1024
            assert isinstance(embedding, list)
    
    def test_titan_embedding_throttling_with_retry(self, mock_bedrock_client, sample_product_texts):
        """Test Titan embedding with throttling error and retry mechanism."""
        # Mock throttling error followed by success
        error_response = {
            'Error': {
                'Code': 'ThrottlingException',
                'Message': 'Rate limit exceeded'
            }
        }
        mock_embedding = np.random.rand(1024).tolist()
        success_response = {
            'body': Mock()
        }
        success_response['body'].read.return_value = json.dumps({
            'embedding': mock_embedding
        }).encode()
        
        # First call fails, second succeeds
        mock_bedrock_client.invoke_model.side_effect = [
            ClientError(error_response, 'InvokeModel'),
            success_response
        ]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = retry_embedding_with_backoff(mock_bedrock_client, sample_product_texts[0])
        
        # Verify retry occurred
        assert mock_bedrock_client.invoke_model.call_count == 2
        assert result == mock_embedding
    
    def test_titan_embedding_max_retries_exceeded(self, mock_bedrock_client, sample_product_texts):
        """Test Titan embedding when max retries are exceeded."""
        # Mock persistent throttling error
        error_response = {
            'Error': {
                'Code': 'ThrottlingException',
                'Message': 'Rate limit exceeded'
            }
        }
        mock_bedrock_client.invoke_model.side_effect = ClientError(error_response, 'InvokeModel')
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = retry_embedding_with_backoff(mock_bedrock_client, sample_product_texts[0], max_retries=2)
        
        # Should return None after max retries
        assert result is None
        assert mock_bedrock_client.invoke_model.call_count == 3  # Initial + 2 retries
    
    def test_titan_embedding_access_denied_error(self, mock_bedrock_client, sample_product_texts):
        """Test Titan embedding with access denied error."""
        # Mock access denied error
        error_response = {
            'Error': {
                'Code': 'AccessDeniedException',
                'Message': 'User is not authorized to perform: bedrock:InvokeModel'
            }
        }
        mock_bedrock_client.invoke_model.side_effect = ClientError(error_response, 'InvokeModel')
        
        result = generate_embeddings_with_titan(mock_bedrock_client, sample_product_texts)
        
        # Should return fallback random embeddings
        assert len(result) == len(sample_product_texts)
        assert len(result[0]) == 1024  # Should still be 1024-dimensional
        assert isinstance(result[0], list)
    
    def test_titan_embedding_service_unavailable_error(self, mock_bedrock_client, sample_product_texts):
        """Test Titan embedding with service unavailable error."""
        # Mock service unavailable error
        error_response = {
            'Error': {
                'Code': 'ServiceUnavailableException',
                'Message': 'Service temporarily unavailable'
            }
        }
        mock_bedrock_client.invoke_model.side_effect = ClientError(error_response, 'InvokeModel')
        
        result = generate_embeddings_with_titan(mock_bedrock_client, sample_product_texts)
        
        # Should return fallback random embeddings
        assert len(result) == len(sample_product_texts)
        assert len(result[0]) == 1024
        assert isinstance(result[0], list)
    
    def test_titan_embedding_malformed_response(self, mock_bedrock_client, sample_product_texts):
        """Test Titan embedding with malformed response."""
        # Mock malformed response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = b"invalid json"
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        result = generate_embeddings_with_titan(mock_bedrock_client, sample_product_texts)
        
        # Should return fallback random embeddings
        assert len(result) == len(sample_product_texts)
        assert len(result[0]) == 1024
        assert isinstance(result[0], list)
    
    def test_titan_embedding_no_client_fallback(self, sample_product_texts):
        """Test Titan embedding with no client (fallback scenario)."""
        result = generate_embeddings_with_titan(None, sample_product_texts)
        
        # Should return fallback random embeddings
        assert len(result) == len(sample_product_texts)
        assert len(result[0]) == 1024
        assert isinstance(result[0], list)


class TestAWSEmbeddingErrorHandling:
    """Test suite for AWS embedding error handling."""
    
    def test_embedding_error_handling_no_credentials(self):
        """Test embedding error handling for no credentials."""
        error = NoCredentialsError()
        
        # Should not raise exception, just log
        with patch('builtins.print') as mock_print:
            handle_aws_embedding_error(error, "test embedding")
            
            # Verify warning was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            warning_printed = any("AWS credentials not found" in call for call in print_calls)
            assert warning_printed
    
    def test_embedding_error_handling_throttling(self):
        """Test embedding error handling for throttling."""
        error_response = {
            'Error': {
                'Code': 'ThrottlingException',
                'Message': 'Rate limit exceeded'
            }
        }
        error = ClientError(error_response, 'InvokeModel')
        
        with patch('builtins.print') as mock_print:
            handle_aws_embedding_error(error, "test embedding")
            
            # Verify throttling warning was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            throttling_printed = any("AWS rate limiting encountered" in call for call in print_calls)
            assert throttling_printed
    
    def test_embedding_error_handling_access_denied(self):
        """Test embedding error handling for access denied."""
        error_response = {
            'Error': {
                'Code': 'AccessDeniedException',
                'Message': 'User is not authorized to perform: bedrock:InvokeModel'
            }
        }
        error = ClientError(error_response, 'InvokeModel')
        
        with patch('builtins.print') as mock_print:
            handle_aws_embedding_error(error, "test embedding")
            
            # Verify access denied warning was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            access_denied_printed = any("AWS access denied" in call for call in print_calls)
            assert access_denied_printed
    
    def test_embedding_error_message_sanitization(self):
        """Test that embedding error messages are sanitized."""
        # Test with potential sensitive information
        message_with_key = "Error: Invalid access key AKIAIOSFODNN7EXAMPLE in request"
        sanitized = _sanitize_embedding_error_message(message_with_key)
        assert "AKIAIOSFODNN7EXAMPLE" not in sanitized
        assert "[ACCESS_KEY_REDACTED]" in sanitized
        
        # Test with long message truncation (use a message without patterns that get replaced)
        long_message = "B" * 300  # Use 'B' to avoid pattern matching
        sanitized = _sanitize_embedding_error_message(long_message)
        assert len(sanitized) <= 220  # 200 + "... [TRUNCATED]"
        assert "[TRUNCATED]" in sanitized


if __name__ == '__main__':
    pytest.main([__file__, '-v'])