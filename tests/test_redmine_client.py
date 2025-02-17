import pytest
import requests
import os
import sys
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, call

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.redmine_client import RedmineClient, RedmineApiError, CacheManager

@pytest.fixture
def client():
    return RedmineClient('http://test-redmine.com', 'test-api-key', timeout=30, verify_ssl=True)

@pytest.fixture
def mock_time_entries_response():
    return {
        'time_entries': [
            {
                'id': 1,
                'project': {'id': 1, 'name': 'Test Project'},
                'user': {'id': 1, 'name': 'Test User'},
                'activity': {'id': 9, 'name': 'Development'},
                'hours': 8.0,
                'comments': 'Test comment',
                'spent_on': '2024-02-15'
            }
        ],
        'total_count': 1
    }

@pytest.fixture
def mock_projects_response():
    return {
        'projects': [
            {
                'id': 1,
                'name': 'Test Project',
                'identifier': 'test',
                'description': 'Test Description',
                'status': 1
            }
        ],
        'total_count': 1
    }

def test_redmine_client_initialization(client):
    assert client.base_url == 'http://test-redmine.com'
    assert client.api_key == 'test-api-key'
    assert client.session.headers['X-Redmine-API-Key'] == 'test-api-key'
    assert client.session.headers['Content-Type'] == 'application/json'

@patch('requests.Session.get')
def test_get_time_entries(mock_get, client, mock_time_entries_response):
    mock_get.return_value.json.return_value = mock_time_entries_response
    mock_get.return_value.raise_for_status.return_value = None
    
    entries = client.get_time_entries()
    assert len(entries) == 1
    assert entries[0]['id'] == 1
    
    # Test with filters
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    entries = client.get_time_entries(start_date=start_date, end_date=end_date)
    
    # Verify the request parameters
    args, kwargs = mock_get.call_args
    assert kwargs['params']['from'] == start_date.strftime('%Y-%m-%d')
    assert kwargs['params']['to'] == end_date.strftime('%Y-%m-%d')

@patch('requests.Session.get')
def test_get_projects(mock_get, client, mock_projects_response):
    mock_get.return_value.json.return_value = mock_projects_response
    mock_get.return_value.raise_for_status.return_value = None
    
    projects = client.get_projects()
    assert len(projects) == 1
    assert projects[0]['id'] == 1
    assert projects[0]['name'] == 'Test Project'

@patch('requests.Session.get')
def test_pagination(mock_get, client):
    # Create a mock response for each page
    mock_responses = [
        Mock(
            json=Mock(return_value={
                'projects': [{'id': 1, 'name': 'Project 1'}],
                'total_count': 2,
                'limit': 100,
                'offset': 0
            })
        ),
        Mock(
            json=Mock(return_value={
                'projects': [{'id': 2, 'name': 'Project 2'}],
                'total_count': 2,
                'limit': 100,
                'offset': 100
            })
        )
    ]
    
    # Configure the mock to return different responses for each call
    mock_get.side_effect = mock_responses
    
    # Call the method that should make paginated requests
    projects = client.get_projects()
    
    # Verify the results
    assert len(projects) == 2
    assert projects[0]['id'] == 1
    assert projects[1]['id'] == 2
    
    # Check the parameters of each call
    expected_calls = [
        call(
            'http://test-redmine.com/projects.json',
            params={'offset': 0, 'limit': 100},
            timeout=30,
            verify=True
        ),
        call(
            'http://test-redmine.com/projects.json',
            params={'offset': 100, 'limit': 100},
            timeout=30,
            verify=True
        )
    ]
    mock_get.assert_has_calls(expected_calls)

@patch('requests.Session.get')
def test_api_error_handling(mock_get, client):
    mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError('404 Client Error')
    
    with pytest.raises(requests.exceptions.HTTPError):
        client.get_time_entries()

@patch('requests.Session.get')
def test_get_activities(mock_get, client):
    mock_response = {
        'time_entry_activities': [
            {'id': 1, 'name': 'Development'},
            {'id': 2, 'name': 'Design'}
        ]
    }
    mock_get.return_value.json.return_value = mock_response
    mock_get.return_value.raise_for_status.return_value = None
    
    activities = client.get_activities()
    assert len(activities) == 2
    assert activities[0]['name'] == 'Development'
    assert activities[1]['name'] == 'Design'

@patch('requests.Session.get')
def test_get_issue_statuses(mock_get, client):
    mock_response = {
        'issue_statuses': [
            {'id': 1, 'name': 'New'},
            {'id': 2, 'name': 'In Progress'}
        ]
    }
    mock_get.return_value.json.return_value = mock_response
    mock_get.return_value.raise_for_status.return_value = None
    
    statuses = client.get_issue_statuses()
    assert len(statuses) == 2
    assert statuses[0]['name'] == 'New'
    assert statuses[1]['name'] == 'In Progress'

@pytest.fixture
def cached_client():
    return RedmineClient(
        'http://test-redmine.com',
        'test-api-key',
        cache_enabled=True,
        cache_ttl={'activities': 300}  # 5 minutes
    )

@patch('requests.Session.get')
def test_cache_mechanism(mock_get, cached_client):  # Note the order change: mock_get first, then cached_client
    # Setup mock response
    mock_response = {
        'time_entry_activities': [
            {'id': 1, 'name': 'Development'}
        ]
    }
    mock_get.return_value = Mock(
        json=Mock(return_value=mock_response),
        raise_for_status=Mock(return_value=None)
    )
    
    # First call should hit the API
    result1 = cached_client.get_activities()
    assert mock_get.call_count == 1
    
    # Second call should use cache
    result2 = cached_client.get_activities()
    assert mock_get.call_count == 1  # No new API call
    assert result1 == result2

def test_client_initialization_with_ssl_and_timeout(client):
    custom_client = RedmineClient(
        'http://test-redmine.com',
        'test-api-key',
        timeout=60,
        verify_ssl=False
    )
    assert custom_client.timeout == 60
    assert custom_client.verify_ssl is False

@patch('requests.Session.get')
def test_rate_limiting_retry(mock_get, client):
    # Mock a rate limit response followed by a success
    mock_get.side_effect = [
        Mock(
            status_code=429,
            headers={'Retry-After': '1'},
            raise_for_status=Mock(side_effect=requests.exceptions.HTTPError)
        ),
        Mock(
            status_code=200,
            json=Mock(return_value={'projects': []}),
            raise_for_status=Mock(return_value=None)
        )
    ]
    
    result = client.get_projects()
    assert mock_get.call_count == 2

@pytest.mark.parametrize("status_code,expected_message", [
    (401, "Authentication failed. Check your API key."),
    (403, "Insufficient permissions for this request."),
    (404, "Resource not found."),
    (422, "Validation failed: error details")
])
@patch('requests.Session.get')
def test_specific_http_errors(mock_get, client, status_code, expected_message):
    # Create a proper mock response with error details
    mock_response = Mock(
        status_code=status_code,
        json=Mock(return_value={'errors': ['error details']}),
        text="Error occurred",
        reason="Test Error"
    )
    
    # Create a proper HTTPError with the mock response
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_response.raise_for_status.side_effect = http_error
    
    mock_get.return_value = mock_response
    
    with pytest.raises(RedmineApiError) as exc_info:
        client.get_projects()
    
    assert exc_info.value.status_code == status_code
    assert expected_message in str(exc_info.value)

@patch('requests.Session.get')
def test_api_error_handling(mock_get, client):
    # Create a proper mock response with error details
    mock_response = Mock(
        status_code=404,
        json=Mock(return_value={'errors': ['Resource not found']}),
        text="404 Client Error",
        raise_for_status=Mock(side_effect=requests.exceptions.HTTPError('404 Client Error'))
    )
    mock_get.return_value = mock_response

    # Now we expect RedmineApiError instead of HTTPError
    with pytest.raises(RedmineApiError) as exc_info:
        client.get_time_entries()
    
    # Verify the error details
    assert exc_info.value.status_code == 404
    assert "Resource not found" in str(exc_info.value)


@pytest.fixture
def rate_limited_client():
    return RedmineClient(
        'http://test-redmine.com',
        'test-api-key',
        rate_limit_per_second=2.0,
        rate_limit_burst=3
    )

def test_rate_limit_initialization(rate_limited_client):
    """Test that rate limit parameters are properly initialized"""
    assert rate_limited_client.rate_limit_per_second == 2.0
    assert rate_limited_client.rate_limit_burst == 3
    assert hasattr(rate_limited_client, '_last_request_time')
    assert hasattr(rate_limited_client, '_request_times')

@patch('time.time')
@patch('time.sleep')
def test_rate_limit_enforcement(mock_sleep, mock_time, rate_limited_client):
    """Test that rate limiting is properly enforced"""
    # Mock time to return incrementing values with smaller gaps to trigger rate limiting
    mock_time.side_effect = [1.0, 1.1, 1.1, 1.1, 1.2, 1.2]  # Changed time values
    
    # Make multiple requests
    for _ in range(3):
        rate_limited_client._check_rate_limit()
    
    # Verify sleep was called to enforce rate limit
    assert mock_sleep.called
    
    # Extract all sleep durations
    sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
    
    # At least one sleep call should be long enough to maintain rate limit
    assert any(duration >= 0.5 for duration in sleep_calls)

@patch('time.time')
@patch('time.sleep')
def test_burst_limit_handling(mock_sleep, mock_time, rate_limited_client):
    """Test that burst limits are properly enforced"""
    # Create a sequence of incrementing times with larger gaps
    base_time = 1000.0
    # Provide time values with larger increments to simulate actual delays
    time_values = []
    current = base_time
    for _ in range(100):  # Increased number of values significantly
        time_values.append(current)
        current += 0.1  # Larger time increment
    
    mock_time.side_effect = time_values
    
    # Make more requests than burst limit allows
    for i in range(4):  # Burst limit is 3
        try:
            rate_limited_client._check_rate_limit()
        except RateLimitExceeded as e:
            print(f"Request {i} failed with: {str(e)}")
            break
    
    # Verify sleep was called for burst control
    assert mock_sleep.called
    calls = mock_sleep.call_args_list
    
    # Should have slept to handle burst
    assert len(calls) > 0
    
    # At least one sleep call should be for burst control
    sleep_durations = [call[0][0] for call in calls]
    assert any(duration >= 0.3 for duration in sleep_durations), \
        f"No significant sleep for burst control found in durations: {sleep_durations}"

@patch('time.time')
@patch('requests.Session.get')
def test_rate_limit_integration(mock_get, mock_time, rate_limited_client, mock_projects_response):
    """Test rate limiting in actual API calls"""
    mock_get.return_value.json.return_value = mock_projects_response
    mock_get.return_value.raise_for_status.return_value = None
    
    # Mock time to return incrementing values
    start_time = 1000.0
    mock_time.side_effect = [start_time + i * 0.1 for i in range(10)]
    
    # Make multiple API calls
    for _ in range(3):
        rate_limited_client.get_projects()
    
    # Verify number of calls
    assert mock_get.call_count == 3

def test_rate_limit_recovery():
    """Test that rate limiting recovers after waiting"""
    client = RedmineClient(
        'http://test-redmine.com',
        'test-api-key',
        rate_limit_per_second=10.0,
        rate_limit_burst=2
    )
    
    # Make initial requests up to burst limit
    for _ in range(2):
        client._check_rate_limit()
    
    # Wait for rate limit window to pass
    time.sleep(1.1)  # Just over 1 second
    
    # Should be able to make more requests now
    client._check_rate_limit()  # Should not raise any exceptions