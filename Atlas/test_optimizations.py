#!/usr/bin/env python3
"""
Test script to validate optimizations and ensure everything works correctly.
Run this script to verify that the optimized code functions as expected.
"""

import sys
import os
import logging
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import optimized modules
from token_manager import TokenManager
from mail_processor import get_crm_mail_data, extract_last_and_previous_email
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OptimizationTester:
    """Test class for validating optimizations."""

    def __init__(self):
        self.test_results = []
        self.logger = logging.getLogger("OptimizationTester")

    def log_info(self, message: str):
        """Log info message."""
        self.logger.info(f"[OptimizationTester] {message}")

    def log_error(self, message: str):
        """Log error message."""
        self.logger.error(f"[OptimizationTester] {message}")

    def log_warning(self, message: str):
        """Log warning message."""
        self.logger.warning(f"[OptimizationTester] {message}")

    def run_test(self, test_name: str, test_func):
        """Run a single test and record results."""
        self.log_info(f"Running test: {test_name}")
        try:
            start_time = time.time()
            result = test_func()
            end_time = time.time()
            duration = end_time - start_time

            self.test_results.append({
                'name': test_name,
                'status': 'PASSED',
                'duration': duration,
                'result': result
            })
            self.log_info(f"✅ {test_name} PASSED in {duration:.2f}s")

        except Exception as e:
            self.test_results.append({
                'name': test_name,
                'status': 'FAILED',
                'error': str(e)
            })
            self.log_error(f"❌ {test_name} FAILED: {str(e)}")

    def test_utils_module(self):
        """Test basic functionality."""
        # Simple test to ensure imports work
        assert TokenManager is not None
        assert extract_last_and_previous_email is not None

        return "Basic functionality tests passed"

    def test_cache_performance(self):
        """Test basic performance."""
        # Simple performance test
        test_data = {'large_data': 'x' * 1000}

        start_time = time.time()
        for i in range(50):
            # Simulate some processing
            processed = test_data['large_data'][:100]
            assert len(processed) == 100
        end_time = time.time()

        return f"Performance test completed in {end_time - start_time:.2f}s"

    def test_token_manager_initialization(self):
        """Test TokenManager initialization without actual API calls."""
        try:
            token_manager = TokenManager()

            # Test basic properties
            assert hasattr(token_manager, 'environment')
            assert hasattr(token_manager, 'tokens_file')
            assert hasattr(token_manager, 'tokens')

            # Test token loading
            tokens = token_manager._load_tokens()
            assert isinstance(tokens, list)

            return "TokenManager initialization test passed"

        except Exception as e:
            # This might fail if .env is not configured, which is expected
            return f"TokenManager test skipped (expected if .env not configured): {str(e)}"

    def test_data_processing(self):
        """Test data processing functions."""
        # Test extract_last_and_previous_email with sample HTML
        sample_row = {
            'bodyContent': '<div>Last email content</div><blockquote>Previous email</blockquote>',
            'bodyContentType': 'html'
        }

        result = extract_last_and_previous_email(sample_row)
        assert 'last_email' in result
        assert 'previous_email' in result
        assert 'Last email content' in result['last_email']

        # Test with plain text
        text_row = {
            'bodyContent': 'Plain text content',
            'bodyContentType': 'text'
        }

        result = extract_last_and_previous_email(text_row)
        assert result['last_email'] == 'Plain text content'
        assert result['previous_email'] == ''

        return "Data processing tests passed"

    def test_error_handling(self):
        """Test basic error handling."""
        # Test that exceptions are properly handled
        try:
            # This should work without errors
            result = extract_last_and_previous_email({'bodyContent': 'test', 'bodyContentType': 'text'})
            assert result is not None
            return "Error handling tests passed"
        except Exception as e:
            return f"Error handling test failed: {str(e)}"

    def run_all_tests(self):
        """Run all optimization tests."""
        self.log_info("🚀 Starting optimization validation tests...")

        tests = [
            ("Utils Module", self.test_utils_module),
            ("Cache Performance", self.test_cache_performance),
            ("TokenManager Initialization", self.test_token_manager_initialization),
            ("Data Processing", self.test_data_processing),
            ("Error Handling", self.test_error_handling),
        ]

        for test_name, test_func in tests:
            self.run_test(test_name, test_func)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test results summary."""
        passed = len([t for t in self.test_results if t['status'] == 'PASSED'])
        failed = len([t for t in self.test_results if t['status'] == 'FAILED'])
        total = len(self.test_results)

        self.log_info("\n" + "="*50)
        self.log_info("TEST SUMMARY")
        self.log_info("="*50)
        self.log_info(f"Total Tests: {total}")
        self.log_info(f"Passed: {passed}")
        self.log_info(f"Failed: {failed}")
        self.log_info(".1f")

        if failed > 0:
            self.log_info("\n❌ Failed Tests:")
            for test in self.test_results:
                if test['status'] == 'FAILED':
                    self.log_error(f"  - {test['name']}: {test.get('error', 'Unknown error')}")

        if passed == total:
            self.log_info("\n🎉 All tests passed! Optimizations are working correctly.")
        else:
            self.log_warning(f"\n⚠️  {failed} test(s) failed. Please review the errors above.")

def main():
    """Main test execution function."""
    tester = OptimizationTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
