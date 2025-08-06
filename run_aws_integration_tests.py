#!/usr/bin/env python3
"""
Comprehensive test runner for AWS Bedrock integration validation.
This script runs all integration tests to validate the complete AWS Bedrock functionality.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_test_suite(test_file, description):
    """Run a specific test suite and report results."""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    try:
        # Run the test file directly
        result = subprocess.run([
            sys.executable, test_file
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print(result.stdout)
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def run_pytest_suite(test_pattern, description):
    """Run pytest on a specific test pattern."""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, '-m', 'pytest', test_pattern, '-v', '--tb=short'
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print(result.stdout)
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def check_test_environment():
    """Check if the test environment is properly set up."""
    print("Checking test environment...")
    
    # Check if required test files exist
    required_files = [
        'tests/integration/test_aws_bedrock_end_to_end.py',
        'tests/integration/test_aws_bedrock_validation.py',
        'tests/test_aws_integration_comprehensive.py',
        'tests/unit/test_aws_bedrock_unit.py',
        'tests/unit/test_aws_load_data_functions.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (project_root / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        return False
    
    # Check if main application files exist
    app_files = ['app.py', 'load_data.py']
    for file_path in app_files:
        if not (project_root / file_path).exists():
            print(f"❌ Missing application file: {file_path}")
            return False
    
    print("✅ Test environment check passed")
    return True


def main():
    """Run all AWS Bedrock integration tests."""
    print("AWS Bedrock Integration Test Suite")
    print("=" * 60)
    
    # Check test environment
    if not check_test_environment():
        print("❌ Test environment check failed. Exiting.")
        sys.exit(1)
    
    # Track test results
    test_results = []
    
    # 1. Run unit tests for AWS Bedrock functionality
    test_results.append(run_pytest_suite(
        'tests/unit/test_aws_bedrock_unit.py',
        'AWS Bedrock Unit Tests'
    ))
    
    # 2. Run unit tests for AWS load data functions
    test_results.append(run_pytest_suite(
        'tests/unit/test_aws_load_data_functions.py',
        'AWS Load Data Unit Tests'
    ))
    
    # 3. Run comprehensive integration tests
    test_results.append(run_test_suite(
        'tests/test_aws_integration_comprehensive.py',
        'AWS Bedrock Comprehensive Integration Tests'
    ))
    
    # 4. Run end-to-end integration tests
    test_results.append(run_test_suite(
        'tests/integration/test_aws_bedrock_end_to_end.py',
        'AWS Bedrock End-to-End Integration Tests'
    ))
    
    # 5. Run requirements validation tests
    test_results.append(run_test_suite(
        'tests/integration/test_aws_bedrock_validation.py',
        'AWS Bedrock Requirements Validation Tests'
    ))
    
    # 6. Run caching and streaming tests
    test_results.append(run_pytest_suite(
        'tests/test_aws_caching_streaming.py',
        'AWS Bedrock Caching and Streaming Tests'
    ))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUITE SUMMARY")
    print(f"{'='*60}")
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"Total test suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ AWS Bedrock integration is fully validated and ready for production")
        
        # Print validation summary
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print(f"{'='*60}")
        print("✅ Complete data loading workflow with AWS Bedrock embeddings")
        print("✅ Personalized description generation with Amazon Nova Pro")
        print("✅ Backend switching functionality (LOCAL ↔ GCP ↔ AWS)")
        print("✅ Vector search performance with 1024-dimensional embeddings")
        print("✅ Error handling and fallback mechanisms")
        print("✅ Caching consistency across all backends")
        print("✅ Streaming endpoint compatibility")
        print("✅ All specification requirements validated")
        
        return 0
    else:
        print(f"\n❌ {total_tests - passed_tests} TEST SUITE(S) FAILED")
        print("Please review the failed tests and fix any issues before deployment")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)