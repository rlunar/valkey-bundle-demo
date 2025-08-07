# Valkey-Powered Personalized Product Search Demo

## Overview

This project demonstrates a modern, AI-powered e-commerce search experience using **Valkey** (Redis fork) with Vector Search capabilities. The application combines traditional keyword search with advanced vector similarity search to provide personalized product recommendations.

## Architecture

### Core Components

- **Backend**: Flask web application (`app.py`)
- **Database**: Valkey with Vector Search module
- **AI Models**:
  - Local: Ollama (tinyllama) + sentence-transformers
  - Google Cloud: Gemini + Vertex AI embeddings
  - AWS Bedrock: Nova Pro + Titan Text Embeddings v2
- **Frontend**: HTML templates with Server-Sent Events (SSE)

### Key Features

- **Hybrid Search**: Combines keyword filtering with vector similarity
- **Personalization**: User profile embeddings for tailored results
- **AI-Generated Content**: Personalized product descriptions
- **High-Performance Caching**: LLM response caching in Valkey
- **Real-time Updates**: SSE for dynamic content loading
- **MMR Reranking**: Maximal Marginal Relevance for result diversification

## Project Structure

```bash
valkey-bundle-demo/
├── app.py                 # Main Flask application
├── load_data.py          # Data loading and embedding generation
├── requirements.txt      # Python dependencies
├── data/
│   ├── electronics_product.csv  # Product dataset
│   └── personas.csv             # User personas
├── templates/
│   ├── layout.html       # Base template
│   ├── home.html         # Product grid
│   ├── login.html        # User authentication
│   └── product_detail.html  # Product details
├── static/
│   └── style.css         # Application styles
└── docs/
    └── README.md         # This documentation
```

## Data Models

### Product Schema

```python
{
    'id': int,                    # Unique identifier
    'name': str,                  # Product name
    'brand': str,                 # Extracted brand
    'main_category': str,         # Primary category
    'sub_category': str,          # Secondary category
    'price': float,               # Current price
    'rating': float,              # Average rating
    'review_count': int,          # Number of reviews
    'image_url': str,             # Product image
    'link': str,                  # External link
    'search_tags': str,           # Comma-separated tags
    'region': str,                # Geographic region
    'embedding': bytes            # Vector embedding (384/768/1024 dims)
}
```

### User Schema

```python
{
    'id': str,                    # User identifier
    'name': str,                  # Display name
    'bio': str,                   # User description
    'purchase_history': str,      # JSON string of past purchases
    'embedding': bytes,           # User preference vector
    'avatar': str                 # Base64 SVG avatar
}
```

## API Endpoints

### Authentication

- `GET /login` - Login form
- `POST /login` - User authentication
- `GET /logout` - Session termination

### Product Discovery

- `GET /` or `/home` - Product homepage
- `POST /search` - Keyword + vector search
- `GET /product/<id>` - Product details with recommendations

### Real-time Features

- `GET /stream/<cache_key>` - SSE endpoint for AI-generated content

## Search Implementation

### Hybrid Search Process

1. **Keyword Filtering**: Tag-based filtering using Valkey's TAG fields
2. **Vector Search**: KNN search using user embedding as query vector
3. **MMR Reranking**: Diversification using Maximal Marginal Relevance
4. **Personalization**: Results tailored to user preferences

### Search Query Structure

```python
# Valkey FT.SEARCH query
query = f"({tag_filter})=>[KNN 25 @embedding $user_vec]"
```

### MMR Algorithm

```python
def mmr_rerank(query_embedding, candidate_embeddings, lambda_param=0.7, top_n=5):
    # Maximal Marginal Relevance reranking to diversify results
    # lambda_param: 1.0 = pure relevance, 0.0 = pure diversity
```

## AI Integration

### Error Handling and Resilience

The application implements comprehensive error handling for all AI backends:

#### AWS Bedrock Error Handling
- **Credential Validation**: Automatic detection and validation of AWS credentials
- **Rate Limiting**: Exponential backoff retry mechanism for throttling
- **Circuit Breaker**: Prevents cascading failures when AWS services are unavailable
- **Graceful Fallbacks**: Application continues functioning with mock responses when AWS is unavailable
- **Security**: Error message sanitization to prevent sensitive information exposure

#### Error Recovery Patterns
```python
# Circuit breaker pattern for AWS service protection
aws_circuit_breaker = AWSCircuitBreaker(failure_threshold=5, recovery_timeout=60)

# Retry with exponential backoff for rate limiting
def retry_with_exponential_backoff(func, max_retries=3, base_delay=1.0):
    # Implementation handles ThrottlingException with progressive delays

# Comprehensive error handling for different AWS error types
def handle_aws_error(error, context, user_name=None, product_name=None):
    # Handles NoCredentialsError, ClientError, network timeouts, etc.
```

### Local Mode (Default)

- **LLM**: Ollama with tinyllama (1.1B parameters)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (384 dims)
- **Advantages**: Privacy, no API costs, offline capability

### Google Cloud Mode (Optional)

- **LLM**: Google Gemini 1.5 Flash
- **Embeddings**: Vertex AI text-embedding-004 (768 dims)
- **Advantages**: Higher quality, faster processing

### AWS Bedrock Mode (Optional)

- **LLM**: Amazon Nova Pro (amazon.nova-pro-v1:0)
- **Embeddings**: Titan Text Embeddings v2 (amazon.titan-embed-text-v2:0, 1024 dims)
- **Advantages**: AWS ecosystem integration, high performance, enterprise-grade AI
- **Requirements**: AWS CLI, proper IAM permissions, supported regions
- **Error Handling**: Comprehensive retry logic, circuit breaker pattern, graceful fallbacks

### Configuration

```python
# Automatic detection based on environment variables (priority order: AWS > GCP > LOCAL)
if os.getenv("AWS_REGION"):
    AI_MODE = "AWS"
    AWS_REGION = os.getenv("AWS_REGION")
    LLM_MODEL_NAME = "amazon.nova-pro-v1:0"
    EMBEDDING_MODEL_NAME = "amazon.titan-embed-text-v2:0"
    VECTOR_DIM = 1024
elif os.getenv("GCP_PROJECT"):
    AI_MODE = "GCP"
else:
    AI_MODE = "LOCAL"
```

## Performance Optimizations

### Caching Strategy

- **LLM Responses**: 2-hour TTL in Valkey
- **Cache Keys**: `llm_cache:user:{user_id}:product:{product_id}`
- **Background Generation**: Async processing with threading

### Vector Search Optimization

- **Index Type**: HNSW (Hierarchical Navigable Small World)
- **Distance Metric**: Cosine similarity
- **Batch Processing**: 100 products per batch during data loading

### Database Schema

```python
# Valkey index creation
FT.CREATE products ON HASH PREFIX 1 product: SCHEMA
  brand_tags TAG SEPARATOR ,
  search_tags TAG SEPARATOR ,
  region TAG
  price NUMERIC
  rating NUMERIC
  review_count NUMERIC
  embedding VECTOR HNSW 6 TYPE FLOAT32 DIM {VECTOR_DIM} DISTANCE_METRIC COSINE
```

## Setup Instructions

### Prerequisites

- Docker (for Valkey)
- Python 3.10+
- Optional: Google Cloud SDK (for cloud mode)

### Quick Start

```bash
# 0. Pull valkey-bundle from the container registry
docker pull valkey/valkey-bundle:8-alpine

# 1. Start Valkey
docker run -d --rm --name valkey-demo -p 6379:6379 valkey/valkey-bundle:8-alpine

# 2. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Install and setup Ollama (local mode)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull tinyllama

# 4. Load data and generate embeddings
python3 load_data.py

# 5. Run the application
flask run --host=0.0.0.0 --port=5001
```

### Google Cloud Mode Setup

```bash
# Set environment variables
export GCP_PROJECT="your-project-id"
export GCP_LOCATION="us-central1"

# Authenticate with Google Cloud
gcloud auth application-default login

# Load data with cloud embeddings
python3 load_data.py --project your-project-id
```

### AWS Bedrock Mode Setup

For detailed AWS Bedrock setup instructions, see [AWS Bedrock Setup Guide](aws-bedrock-setup.md).

#### Quick Setup:
```bash
# Install AWS CLI (if not already installed)
brew install awscli  # macOS
# or follow AWS CLI installation guide for other platforms

# Configure AWS credentials (choose one method)
aws configure  # Interactive setup
# OR set environment variables:
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# Verify AWS configuration and Bedrock access
aws sts get-caller-identity
aws bedrock list-foundation-models --region us-east-1
aws bedrock get-foundation-model --model-identifier amazon.nova-pro-v1:0 --region us-east-1

# Load data with AWS embeddings
python3 load_data.py --aws-region us-east-1

# Run application
flask run --host=0.0.0.0 --port=5001
```

#### Required IAM Permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:ListFoundationModels",
                "bedrock:GetFoundationModel"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/amazon.nova-pro-v1:0",
                "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0"
            ]
        }
    ]
}
```

#### Supported AWS Regions:
- `us-east-1` (N. Virginia) - **Recommended**
- `us-west-2` (Oregon)
- `eu-west-1` (Ireland)

**Note:** Model availability may vary by region. Check the [AWS Bedrock documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html) for current information.

## Development

### Adding New Features

1. **New Search Filters**: Modify the search query in `app.py`
2. **Additional AI Models**: Update the AI configuration section
3. **Custom Personas**: Edit `data/personas.csv`
4. **UI Changes**: Modify templates and `static/style.css`

### Testing Different Configurations

```bash
# Test with cluster mode
python3 load_data.py --cluster
flask run --cluster

# Test with different batch sizes
python3 load_data.py --batch-size 50

# Flush and reload data
python3 load_data.py --flush
```

### Monitoring and Debugging

- **Valkey Connection**: Check with `docker exec valkey-demo valkey-cli PING`
- **Index Status**: `FT.INFO products` in Valkey CLI
- **Cache Inspection**: Monitor cache hit/miss rates in application logs
- **Vector Dimensions**: Ensure consistency between embedding models

## Deployment Considerations

### Production Checklist

- [ ] Use production WSGI server (Gunicorn, uWSGI)
- [ ] Configure proper secret keys
- [ ] Set up SSL/TLS termination
- [ ] Implement proper authentication
- [ ] Monitor Valkey memory usage
- [ ] Set up backup strategies
- [ ] Configure logging and monitoring

### Scaling Options

- **Horizontal**: Valkey Cluster mode for distributed storage
- **Vertical**: Increase memory for larger datasets
- **Caching**: Redis/Valkey for application-level caching
- **Load Balancing**: Multiple Flask instances behind a load balancer

## Troubleshooting

### Common Issues

1. **Valkey Connection Failed**

   ```bash
   # Check if container is running
   docker ps
   # Restart if needed
   docker restart valkey-demo
   ```

2. **Embedding Dimension Mismatch**
   - Ensure consistent model usage between data loading and application
   - Check `VECTOR_DIM` configuration

3. **Ollama Model Not Found**

   ```bash
   # List available models
   ollama list
   # Pull required model
   ollama pull tinyllama
   ```

4. **AWS Bedrock Access Issues**

   ```bash
   # Check AWS credentials
   aws sts get-caller-identity
   # Verify Bedrock access
   aws bedrock list-foundation-models --region us-east-1
   # Test specific model access
   aws bedrock get-foundation-model --model-identifier amazon.nova-pro-v1:0 --region us-east-1
   # Check IAM permissions for bedrock:InvokeModel
   ```

5. **AWS Rate Limiting Issues**
   - Application includes automatic retry with exponential backoff
   - Monitor usage in AWS CloudWatch
   - Consider requesting quota increases for high-volume usage

6. **AWS Circuit Breaker Activation**
   - Application uses circuit breaker pattern to prevent cascading failures
   - Check logs for "AWS circuit breaker" messages
   - Service will automatically recover when AWS becomes available

7. **AWS Credential Issues**
   - Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set
   - Or use `aws configure` for credential setup
   - For EC2 instances, use IAM roles instead of access keys
   - Check credential expiration for temporary credentials

8. **Memory Issues**
   - Reduce batch size in `load_data.py`
   - Monitor Valkey memory usage
   - Consider using smaller embedding models

9. **AWS Network Connectivity Issues**
   - Check network connectivity to AWS Bedrock endpoints
   - Verify security groups and NACLs allow HTTPS traffic
   - Test with different AWS regions if connectivity issues persist

10. **AWS Model Availability Issues**
    - Verify Nova Pro is available in your selected region
    - Check AWS service status at https://status.aws.amazon.com/
    - Some models may have regional availability restrictions

### Performance Tuning

- **Search Results**: Adjust KNN parameter (default: 25)
- **MMR Parameters**: Tune lambda_param for relevance vs diversity
- **Cache TTL**: Modify based on content freshness requirements (default: 2 hours)
- **Index Parameters**: Optimize HNSW configuration for your dataset
- **AWS Bedrock Optimization**:
  - Use batch processing for embedding generation
  - Implement request caching to reduce API calls
  - Monitor CloudWatch metrics for optimization opportunities
  - Consider regional proximity for lower latency

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the terms specified in the LICENSE file.

## Support

For issues and questions:

1. Check this documentation
2. Review the troubleshooting section
3. Check existing GitHub issues
4. Create a new issue with detailed information

---

*This documentation covers the core functionality and setup. For specific implementation details, refer to the source code comments and docstrings.*
