import pytest
import os
import sys

# Add the project root directory to Python path for all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def sample_project_data():
    return {
        'id': 1,
        'name': 'Test Project',
        'description': 'A test project',
        'created_on': '2024-01-01T00:00:00Z',
        'updated_on': '2024-02-15T00:00:00Z'
    }

@pytest.fixture
def test_environment():
    """Setup test environment variables"""
    os.environ['REDMINE_URL'] = 'http://test-redmine.com'
    os.environ['REDMINE_API_KEY'] = 'test-api-key'
    yield
    # Clean up
    del os.environ['REDMINE_URL']
    del os.environ['REDMINE_API_KEY']