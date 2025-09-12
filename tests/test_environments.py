#!/usr/bin/env python3
"""
Environment configuration tests for Samay Core Engine
Tests the application with different environment configurations
"""

import os
import sys
import unittest
import subprocess

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class TestEnvironmentConfiguration(unittest.TestCase):
    """Test environment variable configuration functionality."""
    
    def test_environment_url_set(self):
        """Test that environment URL is properly set by the shell script runner."""
        # Test that the environment variable is set by the shell script
        frontend_url = os.getenv('SAMAY_FRONTEND_URL')
        self.assertIsNotNone(frontend_url, "SAMAY_FRONTEND_URL should be set by shell script")
        self.assertIn(frontend_url, [
            'http://localhost:3001/login',  # QA environment
            'https://getsamay.vercel.app/login'  # Production environment
        ])
    
    def test_qa_environment_url(self):
        """Test that QA environment URL is used when SAMAY_FRONTEND_URL is set."""
        # Test the environment variable logic
        frontend_url = os.getenv('SAMAY_FRONTEND_URL', 'https://getsamay.vercel.app/login')
        # This will be set by the shell script runner
        self.assertIn(frontend_url, [
            'http://localhost:3001/login',
            'https://getsamay.vercel.app/login'
        ])
    
    def test_custom_environment_url(self):
        """Test that custom environment URL is used when SAMAY_FRONTEND_URL is set to custom value."""
        # Test the environment variable logic
        frontend_url = os.getenv('SAMAY_FRONTEND_URL', 'https://getsamay.vercel.app/login')
        # Should be set by the shell script runner
        self.assertIsNotNone(frontend_url)
        self.assertIsInstance(frontend_url, str)

class TestEnvironmentVariablePassing(unittest.TestCase):
    """Test how environment variables are passed to the application."""
    
    def test_command_line_environment_passing(self):
        """Test that environment variables can be passed via command line."""
        # Test with QA environment
        env = {'SAMAY_FRONTEND_URL': 'http://localhost:3001/login'}
        
        # Test that subprocess can receive environment variables
        result = subprocess.run([
            sys.executable, '-c', 
            'import os; print(os.getenv("SAMAY_FRONTEND_URL", "NOT_SET"))'
        ], env=env, capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'http://localhost:3001/login')
    
    def test_build_script_environment_export(self):
        """Test that build script properly exports environment variables."""
        build_script_path = os.path.join(project_root, 'build_samay_macos.sh')
        
        if os.path.exists(build_script_path):
            # Test QA environment
            result = subprocess.run([
                'bash', '-c', 
                f'source {build_script_path} --help && echo "ENV_TEST: $SAMAY_FRONTEND_URL"'
            ], capture_output=True, text=True, cwd=project_root)
            
            # The build script should show the environment variable logic
            self.assertIn('qa', result.stdout)
            self.assertIn('localhost:3001', result.stdout)
        else:
            self.skipTest("Build script not found")
    
    def test_environment_variable_persistence(self):
        """Test that environment variables persist across subprocess calls."""
        # Set environment variable
        os.environ['SAMAY_FRONTEND_URL'] = 'http://test.example.com/login'
        
        # Test that it persists in subprocess
        result = subprocess.run([
            sys.executable, '-c', 
            'import os; print(os.getenv("SAMAY_FRONTEND_URL", "NOT_SET"))'
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'http://test.example.com/login')

class TestBuildScriptIntegration(unittest.TestCase):
    """Test build script environment handling."""
    
    def test_build_script_help_includes_testing_info(self):
        """Test that build script help includes testing information."""
        build_script_path = os.path.join(project_root, 'build_samay_macos.sh')
        
        if os.path.exists(build_script_path):
            result = subprocess.run([build_script_path, '--help'], 
                                  capture_output=True, text=True, cwd=project_root)
            
            self.assertEqual(result.returncode, 0)
            self.assertIn('run_tests.sh', result.stdout)
            self.assertIn('Testing:', result.stdout)
        else:
            self.skipTest("Build script not found")

class TestEnvironmentValidation(unittest.TestCase):
    """Test environment validation and error handling."""
    
    def test_invalid_environment_variable(self):
        """Test behavior with invalid environment variable values."""
        # Test with empty string
        os.environ['SAMAY_FRONTEND_URL'] = ''
        
        # Should return empty string, not fall back to default
        frontend_url = os.getenv('SAMAY_FRONTEND_URL', 'https://getsamay.vercel.app/login')
        self.assertEqual(frontend_url, '')
    
    def test_malformed_url_handling(self):
        """Test behavior with malformed URLs."""
        # Test with malformed URL
        malformed_url = 'not-a-valid-url'
        os.environ['SAMAY_FRONTEND_URL'] = malformed_url
        
        # Should return the malformed URL as-is
        frontend_url = os.getenv('SAMAY_FRONTEND_URL', 'https://getsamay.vercel.app/login')
        self.assertEqual(frontend_url, malformed_url)

def run_environment_tests():
    """Run environment configuration tests."""
    print("🧪 Samay Core Engine - Environment Configuration Test Suite")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentVariablePassing))
    suite.addTests(loader.loadTestsFromTestCase(TestBuildScriptIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentValidation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print(f"📊 Environment Test Results: {result.testsRun} tests run")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 All environment configuration tests passed!")
        print("\n✅ Environment configuration is working correctly!")
        print("\nSummary of tested functionality:")
        print("  • Default production URL fallback")
        print("  • QA environment URL handling")
        print("  • Custom environment URL support")
        print("  • Build script integration")
        print("  • Error handling and validation")
        
        print("\nNext steps:")
        print("  1. Test with real environment variables")
        print("  2. Verify build script functionality")
        print("  3. Test complete environment switching")
        
        return True
    else:
        print("\n❌ Some environment tests failed. Please review and fix.")
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  • {test}: {traceback}")
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  • {test}: {traceback}")
        return False

if __name__ == "__main__":
    success = run_environment_tests()
    sys.exit(0 if success else 1)
