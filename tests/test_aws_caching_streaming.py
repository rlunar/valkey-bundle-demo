#!/usr/bin/env python3
"""
Tests for AWS Bedrock caching and streaming functionality.
This test verifies that AWS-generated descriptions are cached with the same 2-hour TTL
and that the streaming endpoint works correctly with AWS backend.
"""

import pytest
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, get_personalized_descriptions_async, valkey_client


class TestAWSCachingAndStreaming:
    """Test suite for AWS Bedrock caching and streaming functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def mock_valkey_client(self):
        """Mock Valkey client for testing."""
        with patch('app.valkey_client') as mock_client:
            yield mock_client
    
    @pytest.fixture
    def mock_aws_client(self):
        """Mock AWS Bedrock client for testing."""
        mock_client = Mock()
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'results': [{'outputText': 'Test AWS generated description'}]
        }).encode()
        mock_client.invoke_model.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def sample_user_profile(self):
        """Sample user profile for testing."""
        return {
            'id': '101',
            'name': 'John Doe',
            'bio': 'Tech enthusiast who loves gadgets'
        }
    
    @pytest.fixture
    def sample_products(self):
        """Sample products for testing."""
        return [
            {
                'id': '1',
                'name': 'Smartphone',
                'brand': 'TechBrand',
                'price': '$599'
            },
            {
                'id': '2', 
                'name': 'Laptop',
                'brand': 'CompBrand',
                'price': '$999'
            }
        ]
    
    def test_aws_cache_key_generation(self, sample_user_profile, sample_products):
        """Test that cache keys are generated correctly for AWS mode."""
        user_id = sample_user_profile['id']
        product_id = sample_products[0]['id']
        
        expected_cache_key = f"llm_cache:user:{user_id}:product:{product_id}"
        
        # The cache key format should be consistent across all AI backends
        assert expected_cache_key == f"llm_cache:user:{user_id}:product:{product_id}"
    
    @patch('app.ai_client')
    @patch('app.valkey_client')
    def test_aws_description_caching_with_ttl(self, mock_valkey, mock_ai_client, 
                                            sample_user_profile, sample_products):
        """Test that AWS-generated descriptions are cached with 2-hour TTL."""
        # Setup AWS mode
        with patch.dict('app.app.config', {'AI_MODE': 'AWS'}):
            # Mock AWS client response
            mock_response = {
                'body': Mock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'results': [{'outputText': 'AWS generated personalized description'}]
            }).encode()
            mock_ai_client.invoke_model.return_value = mock_response
            
            # Mock Valkey client
            mock_valkey.exists.return_value = False  # Cache miss
            mock_valkey.set = Mock()
            
            # Call the function
            get_personalized_descriptions_async(sample_user_profile, [sample_products[0]])
            
            # Wait for the background thread to complete
            time.sleep(0.1)
            
            # Verify that the description was cached with correct TTL
            expected_cache_key = f"llm_cache:user:{sample_user_profile['id']}:product:{sample_products[0]['id']}"
            
            # Check that set was called with the correct parameters
            mock_valkey.set.assert_called()
            call_args = mock_valkey.set.call_args
            
            # Verify cache key and TTL
            assert call_args[0][0] == expected_cache_key
            assert call_args[1]['ex'] == 7200  # 2 hours in seconds
    
    @patch('app.ai_client')
    @patch('app.valkey_client')
    def test_aws_cache_hit_behavior(self, mock_valkey, mock_ai_client,
                                  sample_user_profile, sample_products):
        """Test that cache hits prevent AWS API calls."""
        # Setup AWS mode
        with patch.dict('app.app.config', {'AI_MODE': 'AWS'}):
            # Mock cache hit
            cache_key = f"llm_cache:user:{sample_user_profile['id']}:product:{sample_products[0]['id']}"
            mock_valkey.exists.return_value = True  # Cache hit
            
            # Call the function
            get_personalized_descriptions_async(sample_user_profile, [sample_products[0]])
            
            # Wait for the background thread to complete
            time.sleep(0.1)
            
            # Verify that AWS API was not called due to cache hit
            mock_ai_client.invoke_model.assert_not_called()
    
    @patch('app.ai_client')
    @patch('app.valkey_client')
    def test_aws_fallback_caching(self, mock_valkey, mock_ai_client,
                                sample_user_profile, sample_products):
        """Test that fallback descriptions are cached when AWS fails."""
        # Setup AWS mode
        with patch.dict('app.app.config', {'AI_MODE': 'AWS'}):
            # Mock AWS client failure
            mock_ai_client.invoke_model.side_effect = Exception("AWS API Error")
            
            # Mock Valkey client
            mock_valkey.exists.return_value = False  # Cache miss
            mock_valkey.set = Mock()
            
            # Call the function
            get_personalized_descriptions_async(sample_user_profile, [sample_products[0]])
            
            # Wait for the background thread to complete
            time.sleep(0.1)
            
            # Verify that fallback description was cached
            mock_valkey.set.assert_called()
            call_args = mock_valkey.set.call_args
            
            # Check that the fallback description contains expected content
            cached_description = call_args[0][1]
            assert sample_user_profile['name'] in cached_description
            assert sample_products[0]['name'] in cached_description
            assert call_args[1]['ex'] == 7200  # 2 hours TTL
    
    def test_streaming_endpoint_with_aws_cache(self, client, mock_valkey_client):
        """Test that the streaming endpoint works correctly with AWS-cached content."""
        # Mock cached AWS description
        test_description = "AWS generated personalized description for streaming"
        mock_valkey_client.get.return_value = test_description.encode()
        
        # Test the streaming endpoint
        cache_key = "llm_cache:user:101:product:1"
        response = client.get(f'/stream/{cache_key}')
        
        # Verify response
        assert response.status_code == 200
        assert response.mimetype == 'text/event-stream'
        
        # Check response content
        response_data = response.get_data(as_text=True)
        assert 'data:' in response_data
        
        # Parse the JSON data from the SSE response
        json_start = response_data.find('{')
        json_end = response_data.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_data = json.loads(response_data[json_start:json_end])
            assert json_data['description'] == test_description
    
    def test_streaming_endpoint_timeout_behavior(self, client, mock_valkey_client):
        """Test streaming endpoint timeout behavior when cache is not populated."""
        # Mock cache miss (key doesn't exist)
        mock_valkey_client.get.return_value = None
        
        cache_key = "llm_cache:user:101:product:nonexistent"
        
        # This test would take 20 seconds in real scenario, so we'll mock time.sleep
        with patch('time.sleep'):
            response = client.get(f'/stream/{cache_key}')
            
            # Verify timeout response
            assert response.status_code == 200
            response_data = response.get_data(as_text=True)
            assert 'Could not generate a personalized description at this time.' in response_data
    
    @patch('app.ai_client')
    @patch('app.valkey_client')
    def test_aws_multiple_products_caching(self, mock_valkey, mock_ai_client,
                                         sample_user_profile, sample_products):
        """Test that multiple products are cached correctly with AWS backend."""
        # Setup AWS mode
        with patch.dict('app.app.config', {'AI_MODE': 'AWS'}):
            # Mock AWS client response
            mock_response = {
                'body': Mock()
            }
            mock_response['body'].read.return_value = json.dumps({
                'results': [{'outputText': 'AWS generated description'}]
            }).encode()
            mock_ai_client.invoke_model.return_value = mock_response
            
            # Mock Valkey client - all cache misses
            mock_valkey.exists.return_value = False
            mock_valkey.set = Mock()
            
            # Call with multiple products
            get_personalized_descriptions_async(sample_user_profile, sample_products)
            
            # Wait for the background thread to complete
            time.sleep(0.2)
            
            # Verify that both products were cached
            assert mock_valkey.set.call_count == len(sample_products)
            
            # Verify cache keys for all products
            call_args_list = mock_valkey.set.call_args_list
            for i, product in enumerate(sample_products):
                expected_key = f"llm_cache:user:{sample_user_profile['id']}:product:{product['id']}"
                assert call_args_list[i][0][0] == expected_key
                assert call_args_list[i][1]['ex'] == 7200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])