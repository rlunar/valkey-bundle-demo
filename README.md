# **Valkey-bundle Powered Personalized Product Search Demo**

## **Introduction**

This project is a fully-functional web application that demonstrates a modern, AI-powered e-commerce experience running entirely on your local machine. It showcases how **Valkey** and its **Vector Search** module can serve as a high-performance, multi-modal backend for complex applications.

The application allows users to log in as different "personas" and receive personalized product recommendations and descriptions based on their interests. These recommendations are generated through a hybrid search that combines traditional keyword filtering with advanced vector similarity search.

**Key features demonstrated:**
* **Multiple AI Backend Options:** Choose between Local (Ollama), Google Cloud (Gemini), or AWS Bedrock (Nova Pro) for AI processing.
* **Hybrid Search:** Combining keyword (tag) search with vector similarity search.  
* **Personalization:** Using user profile embeddings to tailor search results.  
* **AI-Powered Content:** Leveraging advanced language models to generate personalized sales pitches.  
* **High-Performance Caching:** Using Valkey to cache LLM responses, dramatically reducing latency.  
* **Real-time UI Updates:** Using Server-Sent Events (SSE) to push AI-generated content to the browser without a page refresh.
* **Viewed Products Tracking:** Using Valkey Bloom filters to efficiently track which products each user has viewed, with visual indicators (👀) on product cards.

## **Prerequisites**

Before you begin, ensure you have the following installed on your system:

* [Docker](https://docs.docker.com/get-docker/)  
* [Python 3.10+](https://www.python.org/downloads/)  
* **Optional AI Backends:**
  * Google Cloud SDK (gcloud) - for Google Gemini integration
  * AWS CLI - for AWS Bedrock integration

## **Setup and Running the Demo**

Follow these steps to get the application running.

### **Step 1: Start the Valkey Server**

We will use the official `valkey/valkey-bundle` Docker image, which comes with the Vector Search module pre-installed. This command starts a Valkey container, names it `valkey-bundle-demo`, and maps the default port 6379.

\# We use \--rm to automatically remove the container when it's stopped, keeping things clean.  
```bash
docker run -d --rm --name valkey-bundle-demo -p 6379:6379 valkey/valkey-bundle
```
**Verify that the container is running:**
```bash
docker ps
```

You should see valkey-bundle-demo in the list. To test the connection, run:
```bash
docker exec valkey-bundle-demo valkey-cli PING
```

The server should reply with PONG.

### **Step 2: Set Up the Python Environment**

It is highly recommended to use a Python virtual environment to manage dependencies.

\# Create a virtual environment named 'venv'  
```bash
python3 -m venv .venv
```
\# Activate the virtual environment  
```bash
source .venv/bin/activate
```

\# Now, install all required Python packages from the requirements file  
```bash
pip install -r requirements.txt
```

### **Step 3: Configure AI Backend**

This demo supports three AI backend options. Choose one based on your preferences and requirements:

## **AI Backend Options Comparison**

| Feature | Local (Ollama) | Google Cloud (Gemini) | AWS Bedrock (Nova Pro) |
|---------|----------------|----------------------|------------------------|
| **Privacy** | ✅ Complete privacy | ⚠️ Data sent to Google | ⚠️ Data sent to AWS |
| **Cost** | ✅ Free after setup | 💰 Pay per API call | 💰 Pay per API call |
| **Internet Required** | ❌ Works offline | ✅ Requires internet | ✅ Requires internet |
| **Setup Complexity** | ⭐⭐ Moderate | ⭐⭐⭐ Complex | ⭐⭐⭐ Complex |
| **Performance** | ⚠️ Depends on hardware | ✅ Fast, consistent | ✅ Fast, consistent |
| **Model Quality** | ⚠️ Good for demos | ✅ High quality | ✅ High quality |
| **Vector Dimensions** | 384 | 768 | 1024 |
| **Embedding Model** | sentence-transformers | Vertex AI Text Embeddings | Titan Text Embeddings v2 |
| **Text Generation Model** | TinyLlama (1.1B params) | Gemini Pro | Amazon Nova Pro |

### **When to Choose Each Option:**

**Choose Local (Ollama) if:**
- Privacy is your top priority
- You want to work offline
- You're doing development/testing
- You have sufficient local compute resources
- Cost is a primary concern

**Choose Google Cloud (Gemini) if:**
- You need high-quality AI responses
- You're already using Google Cloud services
- You want proven, enterprise-grade AI
- Network latency to Google Cloud is low
- You're comfortable with Google's data handling

**Choose AWS Bedrock (Nova Pro) if:**
- You need the latest Amazon AI models
- You're already using AWS services
- You want enterprise-grade AI with AWS integration
- You need the highest dimensional embeddings (1024D)
- You prefer AWS's data handling and compliance

#### **Option A: Local AI (Default - Ollama)**

This option runs everything locally on your machine for privacy and offline capability.

**1\. Install Ollama**

For other operating systems, please follow the [Ollama installation instructions](https://ollama.com/docs/install).
\# Install Ollama on Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

\# Install Ollama on MacOS
```bash
brew install ollama
```

\# Start Ollama service on MacOS
```bash
brew services start ollama
```

**2\. Download the LLM Model**

For this demo, we use tinyllama, a 1.1B parameter model that is very fast on CPUs. Open a terminal and run:
```bash
ollama pull tinyllama
```

#### **Option B: Google Cloud AI (Gemini)**

To use Google's Gemini models, set up your Google Cloud environment:

**1\. Set Environment Variables**
```bash
export GCP_PROJECT="your-project-id"
export GCP_LOCATION="us-central1"
```

**2\. Authenticate with Google Cloud**
```bash
gcloud auth application-default login
```

#### **Option C: AWS Bedrock (Nova Pro)**

To use AWS Bedrock with Amazon Nova Pro, configure your AWS environment:

**1\. Install AWS CLI (if not already installed)**
```bash
# On macOS
brew install awscli

# On Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# On Windows
# Download and run the AWS CLI MSI installer from AWS documentation
```

**2\. Configure AWS Credentials**

Choose one of the following methods:

**Method A: Using AWS CLI (Recommended)**
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, Default region, and output format
```

**Method B: Using Environment Variables**
```bash
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

**Method C: Using IAM Roles (For EC2 instances)**
```bash
# Only set the region when using IAM roles
export AWS_REGION="us-east-1"
# AWS SDK will automatically use the instance's IAM role
```

**3\. Verify AWS Configuration and Model Access**
```bash
# Test basic AWS connectivity
aws sts get-caller-identity

# Verify Bedrock access and list available models
aws bedrock list-foundation-models --region us-east-1

# Test specific model access (Nova Pro)
aws bedrock get-foundation-model --model-identifier amazon.nova-pro-v1:0 --region us-east-1
```

**4\. Required IAM Permissions**

Ensure your AWS user/role has the following permissions:
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

**5\. Supported AWS Regions**

AWS Bedrock with Nova Pro is available in the following regions:
- `us-east-1` (N. Virginia) - **Recommended**
- `us-west-2` (Oregon)
- `eu-west-1` (Ireland)

**Note:** Model availability may vary by region. Check the [AWS Bedrock documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html) for the most current information.

**For detailed AWS setup instructions, see [docs/aws-bedrock-setup.md](docs/aws-bedrock-setup.md).**

### **Step 4: Run the Data Loading Script**

This script generates vector embeddings and populates the Valkey instance with product and user data. The embedding method depends on your chosen AI backend:

**For Local AI (Default):**
```bash
# Uses sentence-transformers library for embeddings (384 dimensions)
python3 load_data.py
```

**For Google Cloud AI:**
```bash
# Uses Vertex AI embeddings (768 dimensions)
python3 load_data.py --project your-project-id
```

**For AWS Bedrock:**
```bash
# Uses Titan Text Embeddings v2 (1024 dimensions)
python3 load_data.py --aws-region us-east-1
```

**Additional Options:**
```bash
# Add --cluster if using Valkey Cluster
python3 load_data.py --cluster

# Flush existing data before loading
python3 load_data.py --flush
```

### **Step 4.5: Initialize Bloom Filters (Optional)**

To enable the "viewed products" feature that shows a 👀 emoji next to products you've already seen:

```bash
# Initialize Bloom filters for tracking viewed products
python3 init_bloom_filters.py

# Add --cluster if using Valkey Cluster
python3 init_bloom_filters.py --cluster
```

This step creates Bloom filters for each user to efficiently track which products they have viewed. The feature works without this step, but initializing the filters provides better performance.
### **Step 5: Run the Web Application**

Finally, run the application.

\# Run the Flask development server  
\# Add the \-- \--cluster flag if connecting to a Valkey Cluster  
```bash
flask run --host=0.0.0.0 --port=5001
```

## **Accessing the Demo**

Your Flask server is now running on port 5001\.

#### **Option A: Direct Access (If running locally)**

If you are running everything on your local laptop, simply open your browser and go to:

* **http://localhost:5001**

#### **Option B: SSH Tunnel (Recommended for GCE VMs)**

To securely access the app running on your GCE VM from your laptop's browser, use an SSH tunnel. This forwards a port from your laptop to the VM.

1. **Open a *new* local terminal window** (keep the Flask server running in the other one).  
2. Run the following command, replacing the user and IP with your own:  
```bash
   ssh -L 8080:localhost:5001 your_user@your_vm_ip
```
3. Now, open the browser **on your laptop** and go to:  
   * **http://localhost:8080**

You will see the login page for the demo application.

## **Additional Documentation**

- **[Configuration Reference](docs/configuration-reference.md)** - Comprehensive guide to all configuration options
- **[AWS Bedrock Setup Guide](docs/aws-bedrock-setup.md)** - Detailed AWS Bedrock configuration instructions
- **[Project Documentation](docs/README.md)** - Technical architecture and development guide

## **Troubleshooting**

### **General Issues**

**Problem: "Connection refused" when connecting to Valkey**
```bash
# Check if Valkey container is running
docker ps

# If not running, start it
docker run -d --rm --name valkey-bundle-demo -p 6379:6379 valkey/valkey-bundle

# Test connection
docker exec valkey-bundle-demo valkey-cli PING
```

**Problem: "ModuleNotFoundError" when running Python scripts**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

### [AWS Bedrock Specific Docs](docs/aws-bedrock.md)

### **Getting Help**

If you continue to experience issues:

1. **Check the application logs** for detailed error messages
2. **Verify your environment variables** are set correctly:
```bash
env | grep -E "(AWS_|GCP_)"
```
3. **Test your AI backend independently** before running the full application
4. **Check AWS/GCP service status** pages for any ongoing issues
5. **Review the requirements.txt** to ensure all dependencies are installed

For AWS-specific issues, also check:
- AWS CloudTrail logs for API call details
- AWS CloudWatch for Bedrock metrics and errors
- AWS Personal Health Dashboard for service notifications

## **Stopping the Demo**

1. **Stop the Flask Server:** Go to the terminal where Flask is running and press CTRL+C.  
2. **Stop the Valkey Container:**  
```bash
    docker stop valkey-bundle-demo
```
   *(Since we started it with \--rm, it will be automatically removed when stopped).*
