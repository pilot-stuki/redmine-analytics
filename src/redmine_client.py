import os
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from math import ceil
from .cache import CacheManager

logger = logging.getLogger(__name__)

class RedmineApiError(Exception):
    """Custom exception for Redmine API errors"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Redmine API Error ({status_code}): {message}")

class RateLimitExceeded(RedmineApiError):
    """Exception raised when rate limit is exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(429, message)

class RedmineClient:
    # Resource types mapping for response keys
    RESOURCE_KEYS = {
        'time_entries.json': 'time_entries',
        'projects.json': 'projects',
        'users.json': 'users',
        'issues.json': 'issues'
    }

    def __init__(self, base_url: str, api_key: str, timeout: int = 30, verify_ssl: bool = True, rate_limit_per_second: float = 10.0, rate_limit_burst: int = 30, cache_enabled: bool = True, cache_ttl: Dict[str, int] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.rate_limit_per_second = rate_limit_per_second
        self.rate_limit_burst = rate_limit_burst
        self._last_request_time = 0.0
        self._request_times = []
        self.session = requests.Session()
        self.session.headers.update({
            'X-Redmine-API-Key': api_key,
            'Content-Type': 'application/json'
        })
        self._cache_enabled = cache_enabled
        self._cache_manager = CacheManager()
        self._default_cache_ttl = 3600  # 1 hour default
        self._cache_ttl = {
            'activities': 3600 * 24,     # 24 hours
            'issue_statuses': 3600 * 24, # 24 hours
            'issue_priorities': 3600 * 24, # 24 hours
            'users': 3600,               # 1 hour
            'projects': 3600,            # 1 hour
            **(cache_ttl or {})
        }

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a GET request to Redmine API with error handling and retry logic."""
        max_retries = 3
        retry_delay = 1  # seconds
        

        for attempt in range(max_retries):
            try:
                self._check_rate_limit()
                response = self.session.get(
                    f"{self.base_url}/{endpoint}",
                    params=params,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', retry_delay))
                    time.sleep(retry_after)
                    continue
                    
                self._handle_response(response)
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff

    def _handle_response(self, response: requests.Response) -> None:
        """Handle different HTTP status codes with specific error messages"""
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    error_msg = ', '.join(error_data['errors'])
            except ValueError:
                pass
                
            if response.status_code == 401:
                raise RedmineApiError(401, "Authentication failed. Check your API key.")
            elif response.status_code == 403:
                raise RedmineApiError(403, "Insufficient permissions for this request.")
            elif response.status_code == 404:
                raise RedmineApiError(404, "Resource not found.")
            elif response.status_code == 422:
                raise RedmineApiError(422, f"Validation failed: {error_msg}")
            else:
                raise RedmineApiError(response.status_code, error_msg)

    def _get_paginated_response(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Make paginated requests to Redmine API.
        Returns concatenated results from all pages.
        """
        all_items = []
        offset = 0
        limit = 100  # Maximum items per page
        total_count = None
        
        # Get the correct response key for this endpoint
        response_key = self.RESOURCE_KEYS.get(endpoint, endpoint.split('.')[0])
        
        while True:
            page_params = {
                'offset': offset,
                'limit': limit,
                **(params or {})
            }
            
            response = self._make_request(endpoint, page_params)
            
            # Get total_count from first response
            if total_count is None:
                total_count = int(response.get('total_count', 0))
            
            # Extract items using the correct key
            items = response.get(response_key, [])
            all_items.extend(items)
            
            # Stop if we've retrieved all items
            if len(all_items) >= total_count:
                break
                
            # Increment offset for next page
            offset += limit
        
        return all_items

    def get_time_entries(self, 
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        project_id: Optional[int] = None,
                        user_id: Optional[int] = None) -> List[Dict]:
        """Fetch time entries with optional filters and pagination."""
        params = {}
        
        if start_date:
            params['from'] = start_date.strftime('%Y-%m-%d')
        if end_date:
            params['to'] = end_date.strftime('%Y-%m-%d')
        if project_id:
            params['project_id'] = project_id
        if user_id:
            params['user_id'] = user_id

        return self._get_paginated_response('time_entries.json', params)

    def get_project_issues(self,
                          project_id: int,
                          status_id: Optional[str] = None) -> List[Dict]:
        """Fetch issues for a specific project with pagination."""
        params = {
            'project_id': project_id,
            'status_id': status_id if status_id else '*'
        }
        return self._get_paginated_response('issues.json', params)

    def get_project_details(self, project_id: int) -> Dict:
        """Fetch detailed information about a specific project."""
        return self._make_request(f'projects/{project_id}.json').get('project', {})

    def get_projects(self) -> List[Dict]:
        """Fetch all accessible projects with pagination."""
        return self._get_paginated_response('projects.json')

    def get_project_tree(self) -> List[Dict]:
        """Get projects with their hierarchy information"""
        projects = self.get_projects()
        project_map = {p['id']: p for p in projects}
        
        # Add children lists to all projects
        for p in projects:
            p['children'] = []
            
        # Build tree structure
        root_projects = []
        for p in projects:
            if 'parent' in p:
                parent_id = p['parent']['id']
                if parent_id in project_map:
                    project_map[parent_id]['children'].append(p)
            else:
                root_projects.append(p)
                
        return root_projects

    def get_time_entries_for_project(self, 
                                   project_id: int,
                                   start_date: datetime,
                                   end_date: datetime,
                                   include_subprojects: bool = True) -> List[Dict]:
        """Get time entries for a project and optionally its subprojects"""
        entries = []
        
        # Get entries for the main project
        entries.extend(self.get_time_entries(
            start_date=start_date,
            end_date=end_date,
            project_id=project_id
        ))
        
        if include_subprojects:
            # Get all projects to find subprojects
            projects = self.get_projects()
            subprojects = [p['id'] for p in projects if 'parent' in p and p['parent']['id'] == project_id]
            
            # Get entries for each subproject
            for subproject_id in subprojects:
                entries.extend(self.get_time_entries_for_project(
                    project_id=subproject_id,
                    start_date=start_date,
                    end_date=end_date,
                    include_subprojects=True
                ))
        
        return entries

    def get_users(self) -> List[Dict]:
        """Fetch all users with pagination."""
        return self._get_paginated_response('users.json')

    def get_activities(self) -> List[Dict]:
        """Fetch all time entry activities with caching."""
        cache_key = 'activities'
        
        if self._cache_enabled:
            cached_data = self._cache_manager.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        activities = self._make_request(
            'enumerations/time_entry_activities.json'
        ).get('time_entry_activities', [])
        
        if self._cache_enabled:
            self._cache_manager.set(
                cache_key,
                activities,
                self._cache_ttl[cache_key]
            )
        
        return activities

    def get_issue_statuses(self) -> List[Dict]:
        """Fetch all issue statuses with caching."""
        cache_key = 'issue_statuses'
        
        if self._cache_enabled:
            cached_data = self._cache_manager.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        statuses = self._make_request(
            'issue_statuses.json'
        ).get('issue_statuses', [])
        
        if self._cache_enabled:
            self._cache_manager.set(
                cache_key,
                statuses,
                self._cache_ttl[cache_key]
            )
        
        return statuses

    def get_issue_priorities(self) -> List[Dict]:
        """Fetch all issue priorities."""
        # No pagination needed for priorities as it's typically a small list
        return self._make_request('enumerations/issue_priorities.json').get('issue_priorities', [])

    def invalidate_cache(self, key: Optional[str] = None) -> None:
        """Invalidate specific or all cache entries."""
        if not self._cache_enabled:
            return
            
        if key is None:
            self._cache_manager.clear()
        else:
            self._cache_manager.invalidate(key)

    def set_cache_ttl(self, key: str, ttl: int) -> None:
        """Update TTL for a specific cache key."""
        self._cache_ttl[key] = ttl

    def _check_rate_limit(self) -> None:
        """
        Implement token bucket rate limiting algorithm.
        Raises RateLimitExceeded if limit is hit.
        """
        current_time = time.time()
        
        # Clean old requests from history
        cutoff_time = current_time - 1.0  # 1 second window
        self._request_times = [t for t in self._request_times if t > cutoff_time]
        
        max_attempts = 10  # Prevent infinite loops
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            
            # Check burst limit
            if len(self._request_times) >= self.rate_limit_burst:
                sleep_time = self._request_times[0] - cutoff_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    current_time = time.time()
                    cutoff_time = current_time - 1.0
                    self._request_times = [t for t in self._request_times if t > cutoff_time]
                    continue
            
            # Check rate limit
            if self._request_times:
                time_since_last = current_time - self._last_request_time
                required_gap = 1.0 / self.rate_limit_per_second
                if time_since_last < required_gap:
                    time.sleep(required_gap - time_since_last)
                    current_time = time.time()
            
            # If we got here, we're good to make the request
            self._last_request_time = current_time
            self._request_times.append(current_time)
            return
        
        raise RateLimitExceeded("Rate limit check exceeded maximum attempts")