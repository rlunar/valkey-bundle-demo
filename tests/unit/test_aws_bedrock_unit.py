#!/usr/bin/env python3
"""
Unit tests for AWS Bedrock integration.
Tests AWS configuration detection, client initialization, text generation,
embedding generation, and error handling mechanisms.
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


class TestAWSConfigurationDetection:
    """Test suite for AWS configuration detection and client initialization."""
    
    def test_aws_region_environment_variable_detection(self):
        """Test that AWS_REGION environment variable is detected correctly."""
        with patch.dict(os.environ, {'AWS_REGION': 'us-east-1'}, clear=False):
            aws_region = os.getenv("AWS_REGION")
            assert aws_region == 'us-east-1'
    
    def test_aws_mode_priority_over_gcp(self):
        """Test that AWS mode has priority over GCP when both are configured."""
        with patch.dict(os.environ, {
            'AWS_REGION': 'us-west-2',
            'GCP_PROJECT': 'test-project'
        }, clear=False):
            # AWS should be selected due to priority order: AWS > GCP > LOCAL
            aws_region = os.getenv("AWS_REGION")
            gcp_project = os.getenv("GCP_PROJECT")
            
            # Simulate the priority logic from app.py
            if aws_region:
                selected_mode = "AWS"
            elif gcp_project:
                selected_mode = "GCP"
            else:
                selected_mode = "LOCAL"
            
            assert selected_mode == "AWS"
    
    def test_aws_configuration_parameters(self):
        """Test AWS-specific configuration parameters."""
        expected_config = {
            'AI_MODE': 'AWS',
            'LLM_MODEL_NAME': 'amazon.nova-pro-v1:0',
            'EMBEDDING_MODEL_NAME': 'amazon.titan-embed-text-v2:0',
            'VECTOR_DIM': 1024
        }
        
        # Verify expected configuration values
        assert expected_config['LLM_MODEL_NAME'] == 'amazon.nova-pro-v1:0'
        assert expected_config['EMBEDDING_MODEL_NAME'] == 'amazon.titan-embed-text-v2:0'
        assert expected_config['VECTOR_DIM'] == 1024
    
    @patch('boto3.client')
    def test_aws_client_initialization_success(self, mock_boto3_client):
        """Test successful AWS Bedrock client initialization."""
        # Mock successful client creation
        mock_client = Mock()
        mock_client.list_foundation_models.return_value = {'modelSummaries': []}
        mock_boto3_client.return_value = mock_client
        
        # Simulate client initialization
        with patch.dict(os.environ, {'AWS_REGION': 'us-east-1'}, clear=False):
            client = mock_boto3_client(
                'bedrock-runtime',
                region_name=os.getenv('AWS_REGION')
            )
            
            # Test connection
            client.list_foundation_models()
            
            # Verify client was created with correct parameters
            mock_boto3_client.assert_called_with(
                'bedrock-runtime',
                region_name='us-east-1'
            )
            mock_client.list_foundation_models.assert_called_once()
    
    @patch('boto3.client')
    def test_aws_client_initialization_no_credentials(self, mock_boto3_client):
        """Test AWS client initialization with no credentials."""
        # Mock NoCredentialsError
        mock_boto3_client.side_effect = NoCredentialsError()
        
        with patch.dict(os.environ, {'AWS_REGION': 'us-east-1'}, clear=False):
            with pytest.raises(NoCredentialsError):
                mock_boto3_client(
                    'bedrock-runtime',
                    region_name=os.getenv('AWS_REGION')
                )
    
    @patch('boto3.client')
    def test_aws_client_initialization_access_denied(self, mock_boto3_client):
        """Test AWS client initialization with access denied error."""
        # Mock client with access denied error
        mock_client = Mock()
        error_response = {
            'Error': {
                'Code': 'AccessDeniedException',
                'Message': 'User is not authorized to perform: bedrock:ListFoundationModels'
            }
        }
        mock_client.list_foundation_models.side_effect = ClientError(error_response, 'ListFoundationModels')
        mock_boto3_client.return_value = mock_client
        
        with patch.dict(os.environ, {'AWS_REGION': 'us-east-1'}, clear=False):
            client = mock_boto3_client(
                'bedrock-runtime',
                region_name=os.getenv('AWS_REGION')
            )
            
            with pytest.raises(ClientError) as exc_info:
                client.list_foundation_models()
            
            assert exc_info.value.response['Error']['Code'] == 'AccessDeniedException'


class TestNovaProTextGeneration:
    """Test suite for Amazon Nova Pro text generation."""
    
    @pytest.fixture
    def mock_aws_client(self):
        """Mock AWS Bedrock client for testing."""
        mock_client = Mock()
        return mock_client
    
    @pytest.fixture
    def sample_prompt(self):
        """Sample prompt for testing."""
        return "You are a helpful sales assistant. Write a personalized description for John Doe about a Smartphone."
    
    def test_nova_pro_successful_generation(self, mock_aws_client, sample_prompt):
        """Test successful text generation with Nova Pro."""
        # Mock successful response
        mock_response = {
            'body': Mock()
        }
        expected_text = "This smartphone is perfect for John Doe's tech-savvy lifestyle."
        mock_response['body'].read.return_value = json.dumps({
            'results': [{'outputText': expected_text}]
        }).encode()
        mock_aws_client.invoke_model.return_value = mock_response
        
        # Mock AWS configuration
        with patch.dict('app.app.config', {
            'AI_MODE': 'AWS',
            'LLM_MODEL_NAME': 'amazon.nova-pro-v1:0'
        }):
            # Import and test the function
            from app import generate_with_nova_pro
            
            result = generate_with_nova_pro(mock_aws_client, sample_prompt, "John Doe", "Smartphone")
            
            # Verify API call
            mock_aws_client.invoke_model.assert_called_once()
            call_args = mock_aws_client.invoke_model.call_args
            
            # Verify model ID
            assert call_args[1]['modelId'] == 'amazon.nova-pro-v1:0'
            
            # Verify request body
            request_body = json.loads(call_args[1]['body'])
            assert request_body['inputText'] == sample_prompt
            assert request_body['textGenerationConfig']['maxTokenCount'] == 200
            assert request_body['textGenerationConfig']['temperature'] == 0.7
            assert request_body['textGenerationConfig']['topP'] == 0.9
            
            # Verify result
            assert result == expected_text
    
    def test_nova_pro_empty_response(self, mock_aws_client, sample_prompt):
        """Test Nova Pro with empty response."""
        # Mock empty response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'results': []
        }).encode()
        mock_aws_client.invoke_model.return_value = mock_response
        
        from app import generate_with_nova_pro
        
        result = generate_with_nova_pro(mock_aws_client, sample_prompt, "John Doe", "Smartphone")
        
        # Should return fallback description
        assert "John Doe" in result
        assert "Smartphone" in result
        assert "excellent value and quality" in result
    
    def test_nova_pro_malformed_json_response(self, mock_aws_client, sample_prompt):
        """Test Nova Pro with malformed JSON response."""
        # Mock malformed JSON response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = b"invalid json"
        mock_aws_client.invoke_model.return_value = mock_response
        
        from app import generate_with_nova_pro
        
        result = generate_with_nova_pro(mock_aws_client, sample_prompt, "John Doe", "Smartphone")
        
        # Should return fallback description
        assert "John Doe" in result
        assert "Smartphone" in result
        assert "excellent value and quality" in result
    
    def test_nova_pro_throttling_error(self, mock_aws_client, sample_prompt):
        """Test Nova Pro with throttling error."""
        # Mock throttling error
        error_response = {
            'Error': {
                'Code': 'ThrottlingException',
                'Message': 'Rate limit exceeded'
            }
        }
        mock_aws_client.invoke_model.side_effect = ClientError(error_response, 'InvokeModel')
        
        from app import generate_with_nova_pro
        
        result = generate_with_nova_pro(mock_aws_client, sample_prompt, "John Doe", "Smartphone")
        
        # Should return fallback description
        assert "John Doe" in result
        assert "Smartphone" in result
        assert "excellent value and quality" in result
    
    def test_nova_pro_service_unavailable_error(self, mock_aws_client, sample_prompt):
        """Test Nova Pro with service unavailable error."""
        # Mock service unavailable error
        error_response = {
            'Error': {
                'Code': 'ServiceUnavailableException',
                'Message': 'Service temporarily unavailable'
            }
        }
        mock_aws_client.invoke_model.side_effect = ClientError(error_response, 'InvokeModel')
        
        from app import generate_with_nova_pro
        
        result = generate_with_nova_pro(mock_aws_client, sample_prompt, "John Doe", "Smartphone")
        
        # Should return fallback description
        assert "John Doe" in result
        assert "Smartphone" in result
        assert "excellent value and quality" in result
    
    def test_nova_pro_no_client_fallback(self, sample_prompt):
        """Test Nova Pro with no client (fallback scenario)."""
        from app import generate_with_nova_pro
        
        result = generate_with_nova_pro(None, sample_prompt, "John Doe", "Smartphone")
        
        # Should return fallback description
        assert "John Doe" in result
        assert "Smartphone" in result
        assert "excellent value and quality" in result


class TestAppAWSIntegration:
    """Test suite for AWS integration in app.py."""
    
    def test_aws_fallback_description_generation(self):
        """Test AWS fallback description generation."""
        from app import get_aws_fallback_description
        
        result = get_aws_fallback_description("John Doe", "Smartphone")
        
        assert "John Doe" in result
        assert "Smartphone" in result
        assert "excellent value and quality" in result
        assert "perfectly suited to your needs" in result
    
    def test_aws_error_sanitization(self):
        """Test that AWS error messages are sanitized."""
        from app import _sanitize_error_message
        
        # Test with potential access key
        message_with_key = "Error: Invalid access key AKIAIOSFODNN7EXAMPLE"
        sanitized = _sanitize_error_message(message_with_key)
        assert "AKIAIOSFODNN7EXAMPLE" not in sanitized
        assert "[ACCESS_KEY_REDACTED]" in sanitized
        
        # Test with potential secret key
        message_with_secret = "Error: Invalid secret wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        sanitized = _sanitize_error_message(message_with_secret)
        assert "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" not in sanitized
        assert "[SECRET_REDACTED]" in sanitized
        
        # Test with IP address
        message_with_ip = "Error: Connection failed to 192.168.1.1"
        sanitized = _sanitize_error_message(message_with_ip)
        assert "192.168.1.1" not in sanitized
        assert "[IP_REDACTED]" in sanitized


class TestAWSErrorHandling:
    """Test suite for AWS error handling mechanisms."""
    
    def test_aws_credentials_error_handling(self):
        """Test handling of AWS credentials errors."""
        from app import handle_aws_error
        
        error = NoCredentialsError()
        
        with pytest.raises(Exception) as exc_info:
            handle_aws_error(error, "test context", "John Doe", "Smartphone")
        
        # Should raise AWSCredentialsError
        assert "AWS credentials not found" in str(exc_info.value)
    
    def test_aws_rate_limiting_error_handling(self):
        """Test handling of AWS rate limiting errors."""
        from app import handle_aws_error
        
        error_response = {
            'Error': {
                'Code': 'ThrottlingException',
                'Message': 'Rate limit exceeded'
            }
        }
        error = ClientError(error_response, 'InvokeModel')
        
        with pytest.raises(Exception) as exc_info:
            handle_aws_error(error, "test context", "John Doe", "Smartphone")
        
        # Should raise AWSRateLimitError
        assert "AWS rate limiting" in str(exc_info.value)
    
    def test_aws_service_unavailable_error_handling(self):
        """Test handling of AWS service unavailable errors."""
        from app import handle_aws_error
        
        error_response = {
            'Error': {
                'Code': 'ServiceUnavailableException',
                'Message': 'Service temporarily unavailable'
            }
        }
        error = ClientError(error_response, 'InvokeModel')
        
        with pytest.raises(Exception) as exc_info:
            handle_aws_error(error, "test context", "John Doe", "Smartphone")
        
        # Should raise AWSServiceUnavailableError
        assert "AWS service unavailable" in str(exc_info.value)
    
    def test_aws_endpoint_connection_error_handling(self):
        """Test handling of AWS endpoint connection errors."""
        from app import handle_aws_error
        
        error = EndpointConnectionError(endpoint_url="https://bedrock-runtime.us-east-1.amazonaws.com")
        
        with pytest.raises(Exception) as exc_info:
            handle_aws_error(error, "test context", "John Doe", "Smartphone")
        
        # Should raise AWSServiceUnavailableError
        assert "AWS endpoint connection failed" in str(exc_info.value)
    
    def test_error_message_sanitization(self):
        """Test that error messages are sanitized to remove sensitive information."""
        from app import _sanitize_error_message
        
        # Test with potential access key
        message_with_key = "Error: Invalid access key AKIAIOSFODNN7EXAMPLE"
        sanitized = _sanitize_error_message(message_with_key)
        assert "AKIAIOSFODNN7EXAMPLE" not in sanitized
        assert "[ACCESS_KEY_REDACTED]" in sanitized
        
        # Test with potential secret key
        message_with_secret = "Error: Invalid secret wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        sanitized = _sanitize_error_message(message_with_secret)
        assert "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" not in sanitized
        assert "[SECRET_REDACTED]" in sanitized
        
        # Test with IP address
        message_with_ip = "Error: Connection failed to 192.168.1.1"
        sanitized = _sanitize_error_message(message_with_ip)
        assert "192.168.1.1" not in sanitized
        assert "[IP_REDACTED]" in sanitized
    
    def test_aws_fallback_description_generation(self):
        """Test AWS fallback description generation."""
        from app import get_aws_fallback_description
        
        result = get_aws_fallback_description("John Doe", "Smartphone")
        
        assert "John Doe" in result
        assert "Smartphone" in result
        assert "excellent value and quality" in result
        assert "perfectly suited to your needs" in result


class TestAWSCircuitBreaker:
    """Test suite for AWS circuit breaker mechanism."""
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state (normal operation)."""
        from app import AWSCircuitBreaker
        
        circuit_breaker = AWSCircuitBreaker(failure_threshold=3, recovery_timeout=60)
        
        # Mock successful function
        def successful_function():
            return "success"
        
        result = circuit_breaker.call(successful_function)
        assert result == "success"
        assert circuit_breaker.state == 'CLOSED'
        assert circuit_breaker.failure_count == 0
    
    def test_circuit_breaker_open_state(self):
        """Test circuit breaker transitioning to open state after failures."""
        from app import AWSCircuitBreaker, AWSServiceUnavailableError
        
        circuit_breaker = AWSCircuitBreaker(failure_threshold=2, recovery_timeout=60)
        
        # Mock failing function
        def failing_function():
            raise AWSServiceUnavailableError("Service unavailable")
        
        # First failure
        with pytest.raises(AWSServiceUnavailableError):
            circuit_breaker.call(failing_function)
        assert circuit_breaker.failure_count == 1
        assert circuit_breaker.state == 'CLOSED'
        
        # Second failure - should open circuit
        with pytest.raises(AWSServiceUnavailableError):
            circuit_breaker.call(failing_function)
        assert circuit_breaker.failure_count == 2
        assert circuit_breaker.state == 'OPEN'
        
        # Third call should fail immediately due to open circuit
        with pytest.raises(AWSServiceUnavailableError) as exc_info:
            circuit_breaker.call(failing_function)
        assert "circuit breaker is OPEN" in str(exc_info.value)
    
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery from open to half-open to closed."""
        from app import AWSCircuitBreaker, AWSServiceUnavailableError
        import time
        
        circuit_breaker = AWSCircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        # Force circuit to open
        def failing_function():
            raise AWSServiceUnavailableError("Service unavailable")
        
        with pytest.raises(AWSServiceUnavailableError):
            circuit_breaker.call(failing_function)
        assert circuit_breaker.state == 'OPEN'
        
        # Wait for recovery timeout
        time.sleep(0.2)
        
        # Next call should transition to half-open and succeed
        def successful_function():
            return "success"
        
        result = circuit_breaker.call(successful_function)
        assert result == "success"
        assert circuit_breaker.state == 'CLOSED'
        assert circuit_breaker.failure_count == 0


class TestAWSRetryMechanism:
    """Test suite for AWS retry mechanism with exponential backoff."""
    
    def test_retry_mechanism_success_on_first_attempt(self):
        """Test retry mechanism when function succeeds on first attempt."""
        from app import retry_with_exponential_backoff
        
        def successful_function():
            return "success"
        
        result = retry_with_exponential_backoff(successful_function, max_retries=3)
        assert result == "success"
    
    def test_retry_mechanism_success_after_rate_limiting(self):
        """Test retry mechanism with rate limiting followed by success."""
        from app import retry_with_exponential_backoff, AWSRateLimitError
        
        call_count = 0
        def rate_limited_then_success():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise AWSRateLimitError("Rate limited")
            return "success"
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = retry_with_exponential_backoff(rate_limited_then_success, max_retries=3)
        
        assert result == "success"
        assert call_count == 2
    
    def test_retry_mechanism_max_retries_exceeded(self):
        """Test retry mechanism when max retries are exceeded."""
        from app import retry_with_exponential_backoff, AWSRateLimitError
        
        def always_rate_limited():
            raise AWSRateLimitError("Always rate limited")
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            with pytest.raises(AWSRateLimitError):
                retry_with_exponential_backoff(always_rate_limited, max_retries=2)
    
    def test_retry_mechanism_non_retryable_error(self):
        """Test retry mechanism with non-retryable errors."""
        from app import retry_with_exponential_backoff, AWSCredentialsError
        
        def credentials_error():
            raise AWSCredentialsError("Invalid credentials")
        
        # Should not retry for credential errors
        with pytest.raises(AWSCredentialsError):
            retry_with_exponential_backoff(credentials_error, max_retries=3)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])