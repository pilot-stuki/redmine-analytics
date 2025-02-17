import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta

class DataProcessor:
    # Custom field IDs mapping
    PAYMENT_STATUS_FIELDS = {
        'TMS_PAYMENT': 25,
        'HOURS_APPROVED': 26,
        'ERROR_TEXT': 62,
        'HOURS_LOADED': 80,
        'WORK_TYPE_CODE': 86
    }

    @staticmethod
    def process_time_entries(time_entries: List[Dict]) -> pd.DataFrame:
        """Convert time entries to a DataFrame and add computed columns."""
        if not time_entries:
            return pd.DataFrame()
        
        # Create initial DataFrame
        df = pd.DataFrame(time_entries)
        
        # Extract nested values
        df['project_name'] = df['project'].apply(lambda x: x.get('name') if x else None)
        df['user_name'] = df['user'].apply(lambda x: x.get('name') if x else None)
        df['activity_name'] = df['activity'].apply(lambda x: x.get('name') if x else None)
        df['issue_id'] = df['issue'].apply(lambda x: x.get('id') if x else None)

        # Process custom fields
        def get_custom_field_value(fields, field_id):
            if not fields:
                return '0'
            field = next((f for f in fields if f.get('id') == field_id), None)
            return field.get('value', '0') if field else '0'

        # Extract original custom field values
        df['tms_payment'] = df['custom_fields'].apply(lambda x: get_custom_field_value(x, 25))
        df['hours_approved'] = df['custom_fields'].apply(lambda x: get_custom_field_value(x, 26))
        df['error_text'] = df['custom_fields'].apply(lambda x: get_custom_field_value(x, 62))
        df['hours_loaded'] = df['custom_fields'].apply(lambda x: get_custom_field_value(x, 80))
        df['work_type_code'] = df['custom_fields'].apply(lambda x: get_custom_field_value(x, 86))

        # Add computed boolean flags
        df['is_paid'] = df['tms_payment'] == '1'
        df['is_approved'] = df['hours_approved'] == '1'
        df['is_loaded'] = df['hours_loaded'] == '1'

        # Convert dates
        for date_col in ['spent_on', 'created_on', 'updated_on']:
            df[date_col] = pd.to_datetime(df[date_col])

        # Add time-based columns
        df['week'] = df['spent_on'].dt.isocalendar().week
        df['month'] = df['spent_on'].dt.month
        df['quarter'] = df['spent_on'].dt.quarter
        df['year'] = df['spent_on'].dt.year

        # Ensure hours is numeric
        df['hours'] = pd.to_numeric(df['hours'], errors='coerce').fillna(0)

        return df

    @staticmethod
    def segment_time_entries(df: pd.DataFrame, 
                           group_by: List[str],
                           agg_functions: Optional[Dict] = None,
                           date_range: Optional[Dict] = None) -> pd.DataFrame:
        """
        Segment time entries with enhanced filtering and aggregation.
        """
        if df.empty:
            # Return empty DataFrame with expected structure
            columns = group_by.copy()
            if agg_functions:
                for col, funcs in agg_functions.items():
                    if isinstance(funcs, list):
                        columns.extend([f"{col}_{func}" for func in funcs])
                    else:
                        columns.append(f"{col}_{funcs}")
            return pd.DataFrame(columns=columns)

        # Apply date filtering if specified
        if date_range:
            start_date = pd.to_datetime(date_range.get('start_date'))
            end_date = pd.to_datetime(date_range.get('end_date'))
            df = df[(df['spent_on'] >= start_date) & (df['spent_on'] <= end_date)]

        # Perform grouping and aggregation
        result = df.groupby(group_by).agg(agg_functions)
        
        # Flatten column names if we have a multi-level index
        if isinstance(result.columns, pd.MultiIndex):
            result.columns = [f"{col[0]}_{col[1]}" for col in result.columns]
        
        return result.reset_index()

    @staticmethod
    def analyze_project_status(issues: List[Dict], 
                             time_entries_df: Optional[pd.DataFrame] = None,
                             reference_date: Optional[datetime] = None) -> Dict:
        """Enhanced project status analysis with time tracking integration."""
        if not issues:
            return {
                'total_issues': 0,
                'open_issues': 0,
                'overdue_issues': 0,
                'priority_distribution': {},
                'status_distribution': {}
            }

        df = pd.DataFrame(issues)
        ref_date = reference_date or datetime.now()

        # Convert due_date to datetime safely
        df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')
        
        # Extract status and priority more safely
        df['status_name'] = df['status'].apply(lambda x: x.get('name') if isinstance(x, dict) else 'Unknown')
        df['priority_name'] = df['priority'].apply(lambda x: x.get('name') if isinstance(x, dict) else 'Normal')

        analysis = {
            'total_issues': len(df),
            'open_issues': len(df[df['status_name'].isin(['New', 'In Progress'])]),
            'overdue_issues': len(df[df['due_date'].notna() & (df['due_date'] < ref_date)]),
            'priority_distribution': df['priority_name'].value_counts().to_dict(),
            'status_distribution': df['status_name'].value_counts().to_dict()
        }

        # Time tracking analysis if time entries are provided
        if time_entries_df is not None and not time_entries_df.empty:
            time_analysis = {
                'total_logged_hours': time_entries_df['hours'].sum(),
                'paid_hours': time_entries_df[time_entries_df['is_paid']]['hours'].sum(),
                'approved_hours': time_entries_df[time_entries_df['is_approved']]['hours'].sum(),
                'hours_per_issue': time_entries_df.groupby('issue_id')['hours'].sum().mean(),
                'active_users': time_entries_df['user_id'].nunique(),
            }
            analysis.update(time_analysis)

        return analysis

    @staticmethod
    def calculate_project_metrics(time_entries_df: pd.DataFrame, 
                                issues_df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Calculate detailed project metrics including costs and efficiency indicators.
        """
        if time_entries_df.empty:
            return {}

        metrics = {
            'time_tracking': {
                'total_hours': time_entries_df['hours'].sum(),
                'paid_ratio': (time_entries_df[time_entries_df['is_paid']]['hours'].sum() / 
                             time_entries_df['hours'].sum() * 100),
                'approval_ratio': (time_entries_df[time_entries_df['is_approved']]['hours'].sum() / 
                                 time_entries_df['hours'].sum() * 100),
                'hours_by_activity': time_entries_df.groupby('activity_name')['hours'].sum().to_dict(),
                'hours_by_user': time_entries_df.groupby('user_name')['hours'].sum().to_dict(),
            }
        }

        if issues_df is not None and not issues_df.empty:
            metrics['issues'] = {
                'completion_rate': issues_df['done_ratio'].mean(),
                'average_duration': (issues_df['updated_on'] - issues_df['created_on']).mean().days,
                'overdue_rate': (len(issues_df[issues_df['due_date'] < datetime.now()]) / 
                               len(issues_df) * 100),
            }

        return metrics

    @staticmethod
    def validate_data_quality(df: pd.DataFrame) -> Dict[str, any]:
        """Validate data quality and consistency."""
        return {
            'missing_values': df.isnull().sum().to_dict(),
            'negative_hours': (df['hours'] < 0).sum(),
            'future_dates': (df['spent_on'] > datetime.now()).sum(),
            'invalid_projects': df['project_name'].isnull().sum(),
            'invalid_users': df['user_name'].isnull().sum()
        }

    @staticmethod
    def validate_data_types(df: pd.DataFrame) -> Dict[str, bool]:
        """Validate expected data types for critical columns"""
        return {
            'dates_valid': all(pd.api.types.is_datetime64_any_dtype(df[col]) 
                             for col in ['spent_on', 'created_on', 'updated_on']),
            'hours_numeric': pd.api.types.is_numeric_dtype(df['hours']),
            'flags_boolean': all(pd.api.types.is_bool_dtype(df[col]) 
                               for col in ['is_paid', 'is_approved', 'is_loaded'])
        }

    @staticmethod
    def analyze_comments(df: pd.DataFrame) -> Dict[str, any]:
        """Analyze comments for patterns and categories."""
        return {
            'has_comments': df['comments'].notna().sum(),
            'avg_comment_length': df['comments'].str.len().mean(),
            'common_prefixes': df['comments'].str.extract(r'^([^:]+):').value_counts().to_dict()
        }

    @staticmethod
    def filter_time_entries(df: pd.DataFrame, 
                          payment_status: Optional[bool] = None,
                          project_name: Optional[str] = None,
                          user_name: Optional[str] = None,
                          min_hours: Optional[float] = None,
                          max_hours: Optional[float] = None) -> pd.DataFrame:
        """Filter time entries based on multiple criteria."""
        mask = pd.Series(True, index=df.index)
        
        if payment_status is not None:
            mask &= df['is_paid'] == payment_status
        if project_name:
            mask &= df['project_name'] == project_name
        if user_name:
            mask &= df['user_name'] == user_name
        if min_hours is not None:
            mask &= df['hours'] >= min_hours
        if max_hours is not None:
            mask &= df['hours'] <= max_hours
            
        return df[mask]