# Configuration Reference

This document provides a comprehensive reference for all configuration options in the AI-powered product search demo.

## Environment Variables

### AI Backend Selection

The application automatically detects the AI backend based on environment variables in this priority order:

1. **AWS Bedrock** (if `AWS_REGION` is set)
2. **Google Cloud** (if `GCP_PROJECT` is set)
3. **Local Ollama** (default fallback)

### AWS Bedrock Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_REGION` | Yes | - | AWS region (e.g., `us-east-1`) |
| `AWS_ACCESS_KEY_ID` | No* | - | AWS access key (*optional if using IAM roles) |
| `AWS_SECRET_ACCESS_KEY` | No* | - | AWS secret key (*optional if using IAM roles) |

**Models Used:**
- Text Generation: `amazon.nova-pro-v1:0`
- Embeddings: `amazon.titan-embed-text-v2:0`
- Vector Dimensions: 1024

### Google Cloud Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GCP_PROJECT` | Yes | - | Google Cloud project ID |
| `GCP_LOCATION` | No | `us-central1` | Vertex AI location |

**Models Used:**
- Text Generation: `gemini-1.5-flash`
- Embeddings: `text-embedding-004`
- Vector Dimensions: 768

### Local Configuration

No environment variables required. Uses:
- Text Generation: Ollama with `tinyllama`
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- Vector Dimensions: 384

### Valkey Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VALKEY_HOST` | No | `localhost` | Valkey server host |
| `VALKEY_PORT` | No | `6379` | Valkey server port |
| `VALKEY_DB` | No | `0` | Valkey database number |
| `VALKEY_PASSWORD` | No | - | Valkey password (if required) |
| `VALKEY_CLUSTER` | No | `false` | Enable cluster mode |

### Application Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLASK_ENV` | No | `development` | Flask environment |
| `FLASK_DEBUG` | No | `true` | Enable debug mode |
| `CACHE_TTL` | No | `7200` | Cache TTL in seconds (2 hours) |

## Command Line Arguments

### Data Loading Script (`load_data.py`)

| Argument | Description | Example |
|----------|-------------|---------|
| `--project` | GCP project ID (enables GCP mode) | `--project my-gcp-project` |
| `--aws-region` | AWS region (enables AWS mode) | `--aws-region us-east-1` |
| `--cluster` | Enable Valkey cluster mode | `--cluster` |
| `--flush` | Flush existing data before loading | `--flush` |
| `--batch-size` | Batch size for processing | `--batch-size 50` |

### Flask Application (`flask run`)

| Argument | Description | Example |
|----------|-------------|---------|
| `--host` | Host to bind to | `--host 0.0.0.0` |
| `--port` | Port to bind to | `--port 5001` |
| `--cluster` | Enable Valkey cluster mode | `--cluster` |

## Configuration Examples

### Example 1: Local Development
```bash
# .env file (or no configuration needed)
# Uses default local setup with Ollama
```

### Example 2: AWS Bedrock Production
```bash
# .env file
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
CACHE_TTL=3600
```

### Example 3: Google Cloud Staging
```bash
# .env file
GCP_PROJECT=my-staging-project
GCP_LOCATION=us-central1
FLASK_ENV=staging
FLASK_DEBUG=false
```

### Example 4: Valkey Cluster
```bash
# .env file
VALKEY_CLUSTER=true
VALKEY_HOST=cluster-node-1.example.com
VALKEY_PORT=7000
```

## Model Specifications

### AWS Bedrock Models

**Amazon Nova Pro (`amazon.nova-pro-v1:0`)**
- Type: Text generation
- Max tokens: 200 (configured)
- Temperature: 0.7
- Top P: 0.9
- Regions: us-east-1, us-west-2, eu-west-1

**Amazon Titan Text Embeddings v2 (`amazon.titan-embed-text-v2:0`)**
- Type: Text embeddings
- Dimensions: 1024
- Normalization: Enabled
- Max input tokens: 8192

### Google Cloud Models

**Gemini 1.5 Flash (`gemini-1.5-flash`)**
- Type: Text generation
- Max tokens: 200 (configured)
- Temperature: 0.7
- Top P: 0.9

**Text Embedding 004 (`text-embedding-004`)**
- Type: Text embeddings
- Dimensions: 768
- Max input tokens: 3072

### Local Models

**TinyLlama (`tinyllama`)**
- Type: Text generation
- Parameters: 1.1B
- Context length: 2048 tokens

**all-MiniLM-L6-v2**
- Type: Text embeddings
- Dimensions: 384
- Max sequence length: 256 tokens

## Performance Tuning

### Search Parameters

| Parameter | Location | Default | Description |
|-----------|----------|---------|-------------|
| KNN neighbors | `app.py` | 25 | Number of vector search results |
| MMR lambda | `app.py` | 0.7 | Relevance vs diversity balance |
| Top results | `app.py` | 5 | Final number of results returned |

### Caching Configuration

| Parameter | Location | Default | Description |
|-----------|----------|---------|-------------|
| Cache TTL | Environment | 7200s | Time-to-live for cached responses |
| Cache prefix | `app.py` | `llm_cache:` | Redis key prefix |

### Vector Index Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| Index type | HNSW algorithm | HNSW |
| Distance metric | Similarity calculation | COSINE |
| Vector dimensions | Embedding size | 384/768/1024 |

## Security Considerations

### AWS Security
- Use IAM roles when possible
- Rotate access keys regularly
- Apply least privilege principles
- Enable CloudTrail logging

### Google Cloud Security
- Use service accounts with minimal permissions
- Enable audit logging
- Rotate service account keys
- Use Workload Identity when possible

### Application Security
- Don't commit credentials to version control
- Use environment variables or secret management
- Enable HTTPS in production
- Implement proper session management

## Troubleshooting Configuration

### Validation Commands

**Test AWS Configuration:**
```bash
aws sts get-caller-identity
aws bedrock list-foundation-models --region $AWS_REGION
```

**Test Google Cloud Configuration:**
```bash
gcloud auth list
gcloud projects describe $GCP_PROJECT
```

**Test Valkey Connection:**
```bash
docker exec valkey-demo valkey-cli PING
```

**Test Ollama:**
```bash
ollama list
curl http://localhost:11434/api/generate -d '{"model":"tinyllama","prompt":"test"}'
```

### Common Configuration Issues

1. **Wrong AI backend detected**
   - Check environment variable precedence
   - Verify only one backend is configured

2. **Vector dimension mismatch**
   - Ensure consistent model usage
   - Reload data after changing backends

3. **Authentication failures**
   - Verify credentials are correctly set
   - Check IAM/service account permissions

4. **Model not available**
   - Verify region support for AWS/GCP models
   - Check model IDs are correct

## Migration Between Backends

When switching between AI backends:

1. **Flush existing data:**
   ```bash
   python3 load_data.py --flush
   ```

2. **Update environment variables**

3. **Reload data with new backend:**
   ```bash
   # For AWS
   python3 load_data.py --aws-region us-east-1
   
   # For GCP
   python3 load_data.py --project your-project-id
   
   # For Local
   python3 load_data.py
   ```

4. **Restart the application**

This ensures vector dimensions and embeddings are consistent across the system.