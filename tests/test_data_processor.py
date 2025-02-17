import pytest
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_processor import DataProcessor

@pytest.fixture
def sample_time_entries():
    return [
        {
            "id": 1267711,
            "project": {
                "id": 784,
                "name": "Campaign_Management"
            },
            "issue": {
                "id": 216285
            },
            "user": {
                "id": 129,
                "name": "Alexander Kozlov"
            },
            "activity": {
                "id": 36,
                "name": "Управление проектом"
            },
            "hours": 176.0,
            "comments": "АК: операционная работа: 12.25",
            "spent_on": "2025-12-31",
            "created_on": "2025-01-23T16:56:53Z",
            "updated_on": "2025-01-23T16:56:53Z",
            "custom_fields": [
                {
                    "id": 25,
                    "name": "Опл. в ТМС",
                    "value": "0"
                },
                {
                    "id": 26,
                    "name": "Часы согласованы",
                    "value": "0"
                },
                {
                    "id": 62,
                    "name": "Текст ошибки",
                    "value": ""
                },
                {
                    "id": 80,
                    "name": "Часы загружены в ТМС",
                    "value": "0"
                },
                {
                    "id": 86,
                    "name": "Код типа работ ТМС",
                    "value": ""
                }
            ]
        },
        {
            "id": 1267710,
            "project": {
                "id": 784,
                "name": "Campaign_Management"
            },
            "issue": {
                "id": 216285
            },
            "user": {
                "id": 129,
                "name": "Alexander Kozlov"
            },
            "activity": {
                "id": 36,
                "name": "Управление проектом"
            },
            "hours": 151.0,
            "comments": "АК: операционная работа: 11.25",
            "spent_on": "2025-11-30",
            "created_on": "2025-01-23T16:56:31Z",
            "updated_on": "2025-01-23T16:56:31Z",
            "custom_fields": [
                {
                    "id": 25,
                    "name": "Опл. в ТМС",
                    "value": "0"
                },
                {
                    "id": 26,
                    "name": "Часы согласованы",
                    "value": "0"
                },
                {
                    "id": 62,
                    "name": "Текст ошибки",
                    "value": ""
                },
                {
                    "id": 80,
                    "name": "Часы загружены в ТМС",
                    "value": "0"
                },
                {
                    "id": 86,
                    "name": "Код типа работ ТМС",
                    "value": ""
                }
            ]
        }
    ]

@pytest.fixture
def sample_issues():
    return [
        {
            "id": 1,
            "subject": "Test Issue 1",
            "status": {"name": "New"},
            "priority": {"name": "Normal"},
            "due_date": "2024-02-10",
            "created_on": "2024-01-01",
            "updated_on": "2024-01-15"
        },
        {
            "id": 2,
            "subject": "Test Issue 2",
            "status": {"name": "In Progress"},
            "priority": {"name": "High"},
            "due_date": "2024-03-01",
            "created_on": "2024-01-15",
            "updated_on": "2024-02-01"
        }
    ]

def test_process_time_entries(sample_time_entries):
    df = DataProcessor.process_time_entries(sample_time_entries)
    
    # Check basic DataFrame properties
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    
    # Check computed columns
    assert 'week' in df.columns
    assert 'month' in df.columns
    assert 'year' in df.columns
    assert 'is_paid' in df.columns
    assert 'is_approved' in df.columns
    assert 'is_loaded' in df.columns
    
    # Check nested columns are extracted
    assert df['project_name'].iloc[0] == "Campaign_Management"
    assert df['user_name'].iloc[0] == "Alexander Kozlov"
    assert df['activity_name'].iloc[0] == "Управление проектом"
    assert df['issue_id'].iloc[0] == 216285
    
    # Check custom fields processing
    assert df['is_paid'].iloc[0] == False  # value "0"
    assert df['is_approved'].iloc[0] == False  # value "0"
    assert df['is_loaded'].iloc[0] == False  # value "0"
    
    # Check data types
    assert pd.api.types.is_datetime64_any_dtype(df['spent_on'])
    assert pd.api.types.is_datetime64_any_dtype(df['created_on'])
    assert pd.api.types.is_datetime64_any_dtype(df['updated_on'])
    assert pd.api.types.is_numeric_dtype(df['hours'])

def test_segment_time_entries(sample_time_entries):
    df = DataProcessor.process_time_entries(sample_time_entries)
    
    # Test grouping by project and payment status
    grouped = DataProcessor.segment_time_entries(
        df,
        group_by=['project_name', 'is_paid'],
        agg_functions={'hours': ['sum', 'count']}
    )
    
    assert isinstance(grouped, pd.DataFrame)
    assert grouped['hours_sum'].iloc[0] == 327.0  # Total hours for unpaid entries
    assert grouped['hours_count'].iloc[0] == 2  # Number of entries

def test_custom_fields_processing(sample_time_entries):
    df = DataProcessor.process_time_entries(sample_time_entries)
    
    # Test custom fields extraction
    assert 'tms_payment' in df.columns
    assert 'hours_approved' in df.columns
    assert 'hours_loaded' in df.columns
    
    # Check boolean flags
    assert not df['is_paid'].any()  # All entries should be unpaid
    assert not df['is_approved'].any()  # All entries should be unapproved
    assert not df['is_loaded'].any()  # All entries should be not loaded

def test_time_aggregations(sample_time_entries):
    df = DataProcessor.process_time_entries(sample_time_entries)
    
    # Test monthly aggregation
    monthly = df.groupby('month')['hours'].sum()
    assert monthly[11] == 151.0  # November hours
    assert monthly[12] == 176.0  # December hours
    
    # Test user aggregation
    user_hours = df.groupby('user_name')['hours'].sum()
    assert user_hours['Alexander Kozlov'] == 327.0  # Total hours for user

def test_analyze_project_status(sample_issues):
    # Use a fixed reference date for testing
    reference_date = datetime(2024, 2, 15)  # One issue should be overdue at this date
    analysis = DataProcessor.analyze_project_status(sample_issues, reference_date=reference_date)
    
    assert isinstance(analysis, dict)
    assert analysis['total_issues'] == 2
    assert analysis['open_issues'] == 2  # Both 'New' and 'In Progress' count as open
    assert analysis['overdue_issues'] == 1  # One issue is overdue
    assert 'priority_distribution' in analysis
    assert 'Normal' in analysis['priority_distribution']
    assert 'High' in analysis['priority_distribution']

def test_analyze_project_status_with_different_dates(sample_issues):
    # Test with a date where no issues are overdue
    early_date = datetime(2024, 2, 1)
    early_analysis = DataProcessor.analyze_project_status(sample_issues, reference_date=early_date)
    assert early_analysis['overdue_issues'] == 0

    # Test with a date where all issues are overdue
    late_date = datetime(2024, 3, 15)
    late_analysis = DataProcessor.analyze_project_status(sample_issues, reference_date=late_date)
    assert late_analysis['overdue_issues'] == 2