### **AWS Bedrock Specific Issues**

**Problem: "NoCredentialsError: Unable to locate credentials"**

**Solution:**
```bash
# Check if AWS CLI is configured
aws configure list

# If not configured, run:
aws configure

# Or set environment variables:
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"
```

**Problem: "AccessDeniedException: User is not authorized to perform: bedrock:InvokeModel"**

**Solution:**
1. Check your IAM permissions include the required Bedrock actions
2. Verify you're using the correct AWS region where Bedrock is available
3. Ensure the models are available in your selected region:
```bash
aws bedrock list-foundation-models --region us-east-1 | grep -E "(nova-pro|titan-embed)"
```

**Problem: "ValidationException: The model identifier is invalid"**

**Solution:**
- Verify Nova Pro is available in your region
- Check the exact model identifier:
```bash
aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[?contains(modelId, `nova-pro`)]'
```

**Problem: "ThrottlingException: Rate exceeded"**

**Solution:**
- AWS Bedrock has rate limits. The application includes automatic retry logic
- For high-volume testing, consider requesting quota increases in AWS Console
- Monitor your usage in AWS CloudWatch

**Problem: Application falls back to mock responses**

**Symptoms:**
- Descriptions like "For an individual like [name], the [product] represents excellent value..."
- Console warnings about AWS connection issues

**Solution:**
1. Check AWS credentials and region configuration
2. Verify network connectivity to AWS Bedrock endpoints
3. Check AWS service status at https://status.aws.amazon.com/
4. Review application logs for specific error messages

**Problem: Vector search returns poor results with AWS backend**

**Solution:**
- Ensure you loaded data with the correct AWS backend:
```bash
python3 load_data.py --aws-region us-east-1 --flush
```
- Verify the vector index was created with 1024 dimensions
- Check that embeddings were generated successfully (no fallback to random vectors)

### **Performance Issues**

**Problem: Slow response times with AWS Bedrock**

**Solution:**
- Check your network latency to the AWS region
- Consider switching to a closer AWS region
- Verify you're not hitting rate limits (check CloudWatch metrics)
- Ensure caching is working (responses should be faster on subsequent requests)

### **Data Loading Issues**

**Problem: "Failed to generate embeddings" during data loading**

**For AWS Bedrock:**
```bash
# Test Titan embeddings directly
aws bedrock invoke-model \
    --model-id amazon.titan-embed-text-v2:0 \
    --body '{"inputText":"test text","dimensions":1024,"normalize":true}' \
    --region us-east-1 \
    output.json

# Check the response
cat output.json
```
