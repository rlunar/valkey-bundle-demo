# Design Document

## Overview

This design document outlines the integration of AWS Bedrock with Amazon Nova Pro as a third AI backend option for the personalized product search application. The integration follows the existing architectural patterns established for GCP and Local backends, ensuring consistency and maintainability while leveraging AWS's AI capabilities.

The design maintains the current dynamic configuration approach where the AI backend is automatically detected based on environment variables, with AWS Bedrock being selected when `AWS_REGION` is present.

## Architecture

### High-Level Architecture

The AWS Bedrock integration extends the existing three-tier architecture:

```bash
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask App     │    │  Data Loading   │    │     Valkey      │
│                 │    │     Script      │    │   (Vector DB)   │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │AI Backend   │ │    │ │AI Backend   │ │    │ │Vector Index │ │
│ │Selection:   │ │    │ │Selection:   │ │    │ │(Dynamic Dim)│ │
│ │- LOCAL      │ │    │ │- LOCAL      │ │    │ │             │ │
│ │- GCP        │ │    │ │- GCP        │ │    │ │- 384 (Local)│ │
│ │- AWS ←NEW   │ │    │ │- AWS ←NEW   │ │    │ │- 768 (GCP)  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ │- 1024 (AWS) │ │
└─────────────────┘    └─────────────────┘    │ └─────────────┘ │
                                              └─────────────────┘
```

### AI Backend Detection Logic

The system will extend the current detection logic to support three backends:

```python
# Priority order: AWS > GCP > LOCAL
if os.getenv("AWS_REGION"):
    AI_MODE = "AWS"
    # AWS Bedrock configuration
elif os.getenv("GCP_PROJECT"):
    AI_MODE = "GCP"
    # Google Gemini configuration
else:
    AI_MODE = "LOCAL"
    # Ollama configuration
```

### AWS Bedrock Service Integration

AWS Bedrock will be integrated using the boto3 library with two primary services:
- **Amazon Nova Pro**: For text generation (personalized descriptions)
- **Amazon Titan Text Embeddings v2**: For vector embeddings (1024 dimensions)

## Components and Interfaces

### 1. Configuration Component

**Location**: Both `app.py` and `load_data.py`

**AWS-specific Configuration**:
```python
# Environment Variables
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")  # Optional if using IAM roles
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")  # Optional if using IAM roles

# Model Configuration
AI_MODE = "AWS"
LLM_MODEL_NAME = "amazon.nova-pro-v1:0"
EMBEDDING_MODEL_NAME = "amazon.titan-embed-text-v2:0"
VECTOR_DIM = 1024
```

### 2. AWS Bedrock Client Initialization

**Location**: Both `app.py` and `load_data.py`

**Implementation Pattern**:
```python
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def initialize_aws_bedrock():
    try:
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=app.config['AWS_REGION']
        )
        # Test connection
        bedrock_client.list_foundation_models()
        return bedrock_client
    except Exception as e:
        print(f"WARNING: Could not initialize AWS Bedrock client. Details: {e}")
        return None
```

### 3. Text Generation Interface

**Location**: `app.py` - `get_personalized_descriptions_async()`

**AWS Implementation**:
```python
def generate_with_nova_pro(client, prompt):
    try:
        response = client.invoke_model(
            modelId="amazon.nova-pro-v1:0",
            body=json.dumps({
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 200,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            })
        )
        response_body = json.loads(response['body'].read())
        return response_body['results'][0]['outputText']
    except Exception as e:
        raise Exception(f"Nova Pro generation failed: {e}")
```

### 4. Embedding Generation Interface

**Location**: `load_data.py` - batch processing section

**AWS Implementation**:
```python
def generate_embeddings_with_titan(client, texts):
    embeddings = []
    for text in texts:
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
            embeddings.append(response_body['embedding'])
        except Exception as e:
            print(f"WARNING: Embedding generation failed for text: {e}")
            # Use random vector as fallback
            embeddings.append(np.random.rand(1024).astype(np.float32).tolist())
    return embeddings
```

### 5. Error Handling and Fallback Mechanisms

**Centralized Error Handling**:
```python
class AWSBedrockError(Exception):
    pass

def handle_aws_error(error, context=""):
    if isinstance(error, NoCredentialsError):
        print(f"AWS Credentials Error {context}: {error}")
    elif isinstance(error, ClientError):
        if error.response['Error']['Code'] == 'ThrottlingException':
            print(f"AWS Rate Limiting {context}: {error}")
        else:
            print(f"AWS Client Error {context}: {error}")
    else:
        print(f"AWS General Error {context}: {error}")
    
    # Return appropriate fallback
    return get_fallback_response(context)
```

## Data Models

### AWS-Specific Configuration Schema

```python
aws_config = {
    'AI_MODE': 'AWS',
    'AWS_REGION': str,
    'LLM_MODEL_NAME': 'amazon.nova-pro-v1:0',
    'EMBEDDING_MODEL_NAME': 'amazon.titan-embed-text-v2:0',
    'VECTOR_DIM': 1024,
    'bedrock_client': boto3.client
}
```

### Request/Response Models

**Nova Pro Text Generation Request**:
```python
nova_request = {
    "inputText": str,
    "textGenerationConfig": {
        "maxTokenCount": int,
        "temperature": float,
        "topP": float
    }
}
```

**Titan Embedding Request**:
```python
titan_request = {
    "inputText": str,
    "dimensions": 1024,
    "normalize": True
}
```

### Vector Index Schema Update

The Valkey vector index will need to support dynamic dimensions:

```python
# Current index creation logic will be extended
if AI_MODE == "AWS":
    VECTOR_DIM = 1024
elif AI_MODE == "GCP":
    VECTOR_DIM = 768
else:  # LOCAL
    VECTOR_DIM = 384

# Index creation remains the same with dynamic VECTOR_DIM
```

## Error Handling

### Error Categories and Responses

1. **Authentication Errors**
   - **Cause**: Invalid AWS credentials
   - **Response**: Log error, use mock descriptions
   - **Fallback**: Continue with other products

2. **Rate Limiting**
   - **Cause**: AWS API throttling
   - **Response**: Implement exponential backoff
   - **Fallback**: Skip current request, continue batch

3. **Model Unavailability**
   - **Cause**: AWS service outage
   - **Response**: Log error, use mock responses
   - **Fallback**: Complete application functionality with mocks

4. **Network Timeouts**
   - **Cause**: Network connectivity issues
   - **Response**: Retry with timeout, then fallback
   - **Fallback**: Mock responses for affected requests

### Fallback Strategy

```python
def get_aws_fallback_description(user_name, product_name):
    return (
        f"For an individual like {user_name}, the {product_name} "
        f"represents excellent value and quality, perfectly suited to your needs."
    )

def get_aws_fallback_embedding():
    return np.random.rand(1024).astype(np.float32)
```

## Testing Strategy

### Unit Testing

1. **Configuration Tests**
   - Test AWS environment variable detection
   - Test client initialization with valid/invalid credentials
   - Test fallback to mock when AWS unavailable

2. **Integration Tests**
   - Test Nova Pro text generation with sample prompts
   - Test Titan embedding generation with sample texts
   - Test error handling for various AWS error scenarios

3. **Compatibility Tests**
   - Test that AWS mode doesn't break existing GCP/Local functionality
   - Test vector dimension consistency across the application
   - Test cache key generation and retrieval

### Integration Testing

1. **End-to-End Workflow**
   - Test complete data loading with AWS embeddings
   - Test personalized description generation in web app
   - Test search functionality with AWS-generated embeddings

2. **Performance Testing**
   - Compare response times across all three backends
   - Test batch processing performance with AWS Bedrock
   - Test concurrent request handling

3. **Error Scenario Testing**
   - Test behavior with invalid AWS credentials
   - Test behavior during AWS service outages
   - Test graceful degradation to mock responses

### Manual Testing Checklist

- [ ] Set AWS environment variables and verify detection
- [ ] Load sample data using AWS Bedrock embeddings
- [ ] Generate personalized descriptions using Nova Pro
- [ ] Verify vector search works with 1024-dimensional embeddings
- [ ] Test error scenarios (invalid credentials, network issues)
- [ ] Verify fallback mechanisms work correctly
- [ ] Test switching between different AI backends

## Implementation Considerations

### Dependencies

New Python packages required:
```
boto3>=1.34.0
botocore>=1.34.0
```

### Environment Variables

Required for AWS mode:
```bash
AWS_REGION=us-east-1
# Optional if using IAM roles:
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Model Availability

- **Amazon Nova Pro**: Available in select AWS regions
- **Titan Text Embeddings v2**: Available in most AWS regions
- **Fallback Strategy**: Always implement mock responses for unavailable regions

### Performance Considerations

1. **Batch Processing**: Process embeddings in batches to optimize API calls
2. **Caching**: Maintain existing 2-hour TTL for generated descriptions
3. **Connection Pooling**: Reuse boto3 clients across requests
4. **Timeout Configuration**: Set appropriate timeouts for AWS API calls

### Security Considerations

1. **Credential Management**: Support IAM roles, avoid hardcoded credentials
2. **Error Logging**: Don't log sensitive information in error messages
3. **Network Security**: Support VPC endpoints for AWS Bedrock if needed
4. **Data Privacy**: Ensure compliance with data handling requirements

This design maintains consistency with the existing architecture while providing robust AWS Bedrock integration with proper error handling and fallback mechanisms.