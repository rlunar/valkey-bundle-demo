# Implementation Plan

- [x] 1. Set up project structure and core infrastructure

  - Create directory structure for models, services, repositories, and utilities
  - Implement configuration management system with environment variable support
  - Create base exception classes and error handling framework
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 8.1, 8.2, 8.3_

- [x] 2. Implement data models and utility classes

  - [x] 2.1 Create core data model classes (UserProfile, Product)

    - Write dataclass definitions with proper typing
    - Add validation methods and serialization support
    - Create unit tests for data model functionality
    - _Requirements: 1.1, 1.2, 1.4_

  - [x] 2.2 Implement DataProcessor utility class

    - Extract and refactor existing utility functions (generate_tags, extract_brand, clean_numeric, generate_avatar_data_uri)
    - Add comprehensive unit tests for all utility functions
    - Ensure backward compatibility with existing data processing
    - _Requirements: 1.1, 1.4, 9.5_

  - [x] 2.3 Create ValkeyClientFactory class
    - Implement factory pattern for creating Valkey client instances
    - Support both standalone and cluster configurations
    - Add connection validation and error handling
    - _Requirements: 2.1, 2.2, 2.4, 8.2_

- [x] 3. Implement repository layer with data access abstraction

  - [x] 3.1 Create BaseRepository abstract class

    - Define common repository interface and shared functionality
    - Implement connection management and error handling
    - Add logging for database operations
    - _Requirements: 3.1, 3.4, 8.1, 8.3_

  - [x] 3.2 Implement UserRepository class

    - Create methods for user profile CRUD operations
    - Handle user embedding storage and retrieval
    - Add comprehensive unit tests with mocked Valkey client
    - _Requirements: 3.1, 3.2, 3.4, 9.1, 9.2_

  - [x] 3.3 Implement ProductRepository class

    - Create methods for product CRUD operations and batch processing
    - Handle product embedding storage and search operations
    - Add comprehensive unit tests with mocked Valkey client
    - _Requirements: 3.1, 3.3, 3.4, 9.2, 9.3_

  - [x] 3.4 Implement CacheRepository class
    - Create methods for LLM response caching with TTL support
    - Handle cache key management and cleanup operations
    - Add unit tests for caching functionality
    - _Requirements: 3.1, 3.4, 9.4_

- [x] 4. Implement service layer for business logic

  - [x] 4.1 Create EmbeddingService interface and implementations

    - Define abstract EmbeddingService interface
    - Implement GCPEmbeddingService for Vertex AI integration
    - Implement LocalEmbeddingService for sentence-transformers
    - Add unit tests for both implementations with proper mocking
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 9.4_

  - [x] 4.2 Create LLMService interface and implementations

    - Define abstract LLMService interface for personalized descriptions
    - Implement GCPLLMService for Google Genai integration
    - Implement LocalLLMService for Ollama integration
    - Add async processing and caching integration
    - Add comprehensive unit tests with mocked AI clients
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 9.4_

  - [x] 4.3 Implement SearchService class

    - Create product search methods combining keyword and vector search
    - Implement MMR reranking algorithm for result diversification
    - Add methods for similar and recommended product retrieval
    - Create comprehensive unit tests for search functionality
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 9.2, 9.3_

  - [x] 4.4 Implement DataLoaderService class
    - Create methods for loading products and personas from CSV files
    - Implement batch processing with progress tracking
    - Add search index creation and database flushing functionality
    - Create unit tests for data loading operations
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 9.5_

- [x] 5. Refactor Flask application to use service architecture

  - [x] 5.1 Create dependency injection container

    - Implement service container for managing dependencies
    - Configure service instances with proper dependency wiring
    - Add configuration-based service selection (GCP vs Local)
    - _Requirements: 6.3, 2.3, 2.4_

  - [x] 5.2 Refactor Flask routes to use services

    - Update login, home, search, and product detail routes
    - Replace direct database calls with service method calls
    - Maintain existing HTTP behavior and response formats
    - Add proper error handling and logging to routes
    - _Requirements: 6.1, 6.2, 6.4, 8.3, 9.1, 9.2, 9.3_

  - [x] 5.3 Update streaming endpoint and async processing
    - Refactor SSE streaming to work with new LLMService
    - Ensure async description generation works with service architecture
    - Maintain existing caching and streaming behavior
    - _Requirements: 6.1, 6.2, 9.4_

- [x] 6. Refactor data loading script to use service architecture

  - [x] 6.1 Create new object-oriented data loading script

    - Replace procedural code with service-based implementation
    - Use DataLoaderService for all data processing operations
    - Maintain existing command-line interface and functionality
    - Add improved error handling and progress reporting
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 8.2, 8.3, 9.5_

  - [x] 6.2 Update argument parsing and configuration
    - Integrate with ConfigurationManager for consistent settings
    - Maintain backward compatibility with existing command-line options
    - Add validation for configuration parameters
    - _Requirements: 2.1, 2.2, 7.1, 9.5_

- [x] 7. Add comprehensive error handling and logging

  - [x] 7.1 Implement logging configuration

    - Set up structured logging throughout the application
    - Configure different log levels for development and production
    - Add request tracing and performance logging
    - _Requirements: 8.1, 8.3_

  - [x] 7.2 Add error handling middleware
    - Create Flask error handlers for custom exceptions
    - Implement graceful degradation for AI service failures
    - Add user-friendly error messages and fallback responses
    - _Requirements: 8.2, 8.3, 4.4_

- [x] 8.1 Write unit tests for all components

  - Create tests for repositories with mocked Valkey clients
  - Create tests for services with mocked dependencies
  - Create tests for utility classes and data models
  - Achieve high code coverage for critical business logic
  - _Requirements: 1.1, 1.2, 1.4_

  - [x] 8.2 Write integration tests
    - Create tests that verify service integration with real Valkey instance
    - Test configuration management with different environment setups
    - Test data loading workflows end-to-end
    - _Requirements: 2.1, 2.2, 7.1, 7.2_

- [x] 9. Final integration and cleanup

  - [x] 9.1 Update project documentation

    - Update README with new architecture information
    - Add code examples showing how to use the new services
    - Document configuration options and deployment instructions
    - _Requirements: 1.1, 2.1_

  - [x] 9.2 Performance testing and optimization

    - Test application performance with refactored architecture
    - Optimize database queries and caching strategies
    - Ensure response times meet or exceed original performance
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 9.3 Final validation and demo preparation
    - Verify all existing functionality works identically
    - Test with both GCP and local AI configurations
    - Prepare demo script showcasing the improved architecture
    - Create deployment guide for production use
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
