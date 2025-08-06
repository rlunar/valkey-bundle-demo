# Implementation Plan

- [x] 1. Add AWS dependencies and update project configuration

  - Add boto3 and botocore to requirements.txt with appropriate versions
  - Update project documentation to include AWS setup instructions
  - _Requirements: 3.3, 5.4_

- [x] 2. Implement AWS Bedrock configuration detection in app.py

  - Extend the existing AI backend detection logic to check for AWS_REGION environment variable
  - Add AWS-specific configuration variables (AI_MODE="AWS", model names, vector dimensions)
  - Initialize boto3 bedrock-runtime client with proper error handling
  - _Requirements: 1.1, 3.1, 3.2, 3.5_

- [x] 3. Implement AWS Bedrock text generation in app.py

  - Add Nova Pro text generation function in the get_personalized_descriptions_async method
  - Implement proper JSON request/response handling for Nova Pro API
  - Add AWS-specific error handling and fallback to mock responses
  - _Requirements: 2.1, 2.2, 2.4, 4.1, 4.4_

- [x] 4. Update caching and streaming functionality for AWS backend

  - Ensure AWS-generated descriptions are cached with the same 2-hour TTL
  - Verify streaming endpoint works correctly with AWS backend
  - Test cache key generation and retrieval for AWS mode
  - _Requirements: 2.3, 2.5_

- [x] 5. Implement AWS Bedrock configuration detection in load_data.py

  - Extend AI backend detection logic to support AWS_REGION environment variable
  - Add AWS-specific configuration (model names, vector dimensions, client initialization)
  - Add command-line argument --aws-region for explicit AWS mode selection
  - _Requirements: 3.1, 3.2, 5.1_

- [x] 6. Implement AWS Bedrock embedding generation in load_data.py

  - Add Titan Text Embeddings v2 integration for batch embedding generation
  - Implement proper error handling for embedding API calls with fallback to random vectors
  - Update batch processing logic to handle AWS embedding responses
  - _Requirements: 1.3, 5.2, 5.3_

- [ ] 7. Update Valkey index creation for dynamic vector dimensions

  - Modify index creation logic to use the correct vector dimension based on AI_MODE
  - Ensure index creation works correctly with 1024-dimensional vectors for AWS
  - Add logging for index creation with dimension information
  - _Requirements: 1.5, 5.4_

- [ ] 8. Implement comprehensive error handling for AWS integration

  - Add specific error handling for AWS credential issues, rate limiting, and service unavailability
  - Implement fallback mechanisms that allow the application to continue functioning
  - Add proper logging for AWS errors without exposing sensitive information
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 9. Add AWS persona embedding generation in load_data.py

  - Update persona processing section to support AWS Bedrock embeddings
  - Implement error handling for persona embedding generation
  - Ensure persona embeddings use the correct 1024-dimensional vectors for AWS
  - _Requirements: 5.2, 5.3_

- [ ] 10. Create unit tests for AWS Bedrock integration

  - Write tests for AWS configuration detection and client initialization
  - Create tests for Nova Pro text generation with mock responses
  - Add tests for Titan embedding generation with error scenarios
  - Write tests for fallback mechanisms and error handling
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 11. Update documentation and configuration examples

  - Add AWS setup instructions to README.md
  - Create example environment variable configurations for AWS mode
  - Document the three AI backend options and their trade-offs
  - Add troubleshooting section for AWS-specific issues
  - _Requirements: 3.3, 3.5_

- [ ] 12. Integration testing and validation
  - Test complete data loading workflow with AWS Bedrock embeddings
  - Verify personalized description generation works end-to-end with Nova Pro
  - Test switching between different AI backends without breaking functionality
  - Validate vector search performance with 1024-dimensional AWS embeddings
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 5.1, 5.2_
