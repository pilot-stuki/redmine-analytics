import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import sys
from pathlib import Path
import io

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.redmine_client import RedmineClient
from src.data_processor import DataProcessor
from src.frontend.components.visualizations import CostAnalyticsVisualizations
from src.frontend.components.auth import Authenticator  # Updated import
from src.frontend.localization import get_text, TRANSLATIONS  # Updated import

# Load environment variables
load_dotenv()

class DashboardApp:
    HOURLY_RATE = 1650  # RUB per hour

    def __init__(self):
        """Initialize with improved secrets handling"""
        try:
            self.auth = Authenticator()
            self.init_session_state()
            
            # Get Redmine credentials
            redmine_url = self._get_secret('REDMINE_URL')
            redmine_api_key = self._get_secret('REDMINE_API_KEY')
            
            if not redmine_url or not redmine_api_key:
                raise ValueError("Missing Redmine credentials")
                
            self.client = self.init_redmine_client(redmine_url, redmine_api_key)
            self.viz = CostAnalyticsVisualizations()

        except Exception as e:
            st.error(f"Initialization error: {str(e)}")
            st.stop()

    def _get_secret(self, key: str, default: str = None) -> str:
        """Get secret from various sources"""
        # Try Streamlit secrets first
        if hasattr(st, 'secrets'):
            if hasattr(st.secrets, 'secrets') and hasattr(st.secrets.secrets, key):
                return getattr(st.secrets.secrets, key)
            if key in st.secrets:
                return st.secrets[key]
                
        # Try environment variables
        env_value = os.getenv(key)
        if env_value:
            return env_value
            
        return default

    @staticmethod
    def init_session_state():
        """Initialize session state with default values"""
        defaults = {
            'language': 'en',
            'selected_range': 'Last 30 days',
            'start_date': datetime.now().date() - timedelta(days=30),
            'end_date': datetime.now().date(),
            'selected_projects': [],
            'data_loaded': False,
            'username': "",
            'user_role': "",
            'authenticated': False
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    @staticmethod
    def init_redmine_client(url: str, api_key: str):
        """Initialize Redmine client with provided credentials"""
        return RedmineClient(
            base_url=url.strip(),
            api_key=api_key.strip()
        )

    @st.cache_data(ttl=300)
    def load_data(_self, start_date, end_date, project_ids=None):
        """Load data for specifically selected projects only"""
        # Ensure we have default project if none selected
        if not project_ids:
            projects = _self.client.get_projects()
            if projects:
                project_ids = [projects[0]['id']]
            else:
                return pd.DataFrame()  # Return empty DataFrame if no projects available

        # Load time entries only for selected projects
        all_entries = []
        processed_entries = set()

        for project_id in project_ids:
            entries = _self.client.get_time_entries(
                start_date=start_date,
                end_date=end_date,
                project_id=project_id
            )
            
            # Add only entries for the specific project
            for entry in entries:
                if entry['id'] not in processed_entries and entry['project']['id'] in project_ids:
                    all_entries.append(entry)
                    processed_entries.add(entry['id'])

        df = DataProcessor.process_time_entries(all_entries)
        
        if not df.empty:
            df['spent_on'] = pd.to_datetime(df['spent_on']).dt.date
            df = df[(df['spent_on'] >= start_date) & (df['spent_on'] <= end_date)]
        
        return df

    def render_language_selector(self):
        """Render language selector in sidebar"""
        with st.sidebar:
            # Language selector at the top
            lang = st.selectbox(
                "Language/Язык",
                options=['en', 'ru'],
                index=0 if st.session_state.language == 'en' else 1,
                key="language_selector"
            )
            if lang != st.session_state.language:
                st.session_state.language = lang
                st.rerun()
            st.markdown("---")

    def render_sidebar(self):
        """Render sidebar with fixed date range handling"""
        with st.sidebar:
            st.header(get_text('filters.header', st.session_state.language))
            
            # Date range selector outside form
            st.subheader(get_text('filters.date_range', st.session_state.language))
            
            # Define date ranges with translated keys
            current_lang = st.session_state.language
            date_ranges = {
                get_text('date_ranges.last_7', current_lang): 7,
                get_text('date_ranges.last_30', current_lang): 30,
                get_text('date_ranges.last_quarter', current_lang): 90,
                get_text('date_ranges.this_year', current_lang): 365,
                get_text('date_ranges.custom', current_lang): None
            }

            # Get current range in current language - fix translation lookup
            if st.session_state.selected_range in TRANSLATIONS['en']['date_ranges']:
                current_range_key = st.session_state.selected_range
            else:
                # Default to 'Last 30 days' if range not found
                current_range_key = 'Last 30 days'
                st.session_state.selected_range = current_range_key

            current_range = get_text(f'date_ranges.{current_range_key.lower().replace(" ", "_")}', current_lang)

            # Select date range
            selected_range = st.selectbox(
                get_text('filters.select_range', current_lang),
                options=list(date_ranges.keys()),
                index=list(date_ranges.keys()).index(current_range) if current_range in date_ranges else 1
            )

            # Store selection in English for consistency
            for en_key in TRANSLATIONS['en']['date_ranges'].keys():
                if (get_text(f'date_ranges.{en_key}', 'en') == selected_range or 
                    get_text(f'date_ranges.{en_key}', 'ru') == selected_range):
                    st.session_state.selected_range = get_text(f'date_ranges.{en_key}', 'en')
                    break

            # Handle date selection
            if selected_range == get_text('date_ranges.custom', current_lang):
                col1, col2 = st.columns(2)
                with col1:
                    end_date = st.date_input(
                        get_text('filters.end_date', current_lang),
                        value=st.session_state.end_date
                    )
                with col2:
                    start_date = st.date_input(
                        get_text('filters.start_date', current_lang),
                        value=st.session_state.start_date
                    )
                st.session_state.start_date = start_date
                st.session_state.end_date = end_date
            else:
                days = date_ranges[selected_range]
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=days)
                st.session_state.start_date = start_date
                st.session_state.end_date = end_date

            # Project selection form
            with st.form("filter_form"):
                st.subheader(get_text('filters.project_filter', st.session_state.language))
                projects = self.client.get_projects()
                project_choices = {p['name']: p['id'] for p in projects}
                
                # Use stored project selection
                default_project = list(project_choices.keys())[0] if project_choices else None
                selected_projects = st.multiselect(
                    get_text('filters.select_projects', st.session_state.language),
                    options=list(project_choices.keys()),
                    default=st.session_state.selected_projects or [default_project] if default_project else None
                )
                
                submitted = st.form_submit_button(
                    label=get_text('filters.apply', st.session_state.language),
                    type="primary",
                    use_container_width=True
                )
                
                if submitted:
                    # Store selected projects
                    st.session_state.selected_projects = selected_projects
                    project_ids = [project_choices[p] for p in selected_projects] if selected_projects else None
                    return start_date, end_date, project_ids

            # Handle first load
            if not st.session_state.data_loaded:
                st.session_state.data_loaded = True
                return (
                    st.session_state.start_date,
                    st.session_state.end_date,
                    [project_choices[default_project]] if default_project else None
                )

            return None, None, None

    def _build_project_choices(self, projects, level=0):
        """Helper method to build project choices dictionary"""
        choices = {}
        for project in projects:
            name = f"{'  ' * level}{project['name']}"
            choices[name] = project['id']
            if project.get('children'):
                choices.update(self._build_project_choices(project['children'], level + 1))
        return choices

    def render_metrics(self, df):
        """Render metrics without redundant date range display"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Calculate metrics directly from the filtered data
        total_hours = df['hours'].sum()
        total_cost = total_hours * self.HOURLY_RATE
        paid_hours = df[df['is_paid']]['hours'].sum()
        approved_hours = df[df['is_approved']]['hours'].sum()
        
        # Render metrics without date range
        with col1:
            st.metric("Total Hours", f"{total_hours:.1f}")
        with col2:
            st.metric("Total Cost (RUB)", f"{total_cost:,.0f}")
        with col3:
            paid_ratio = (paid_hours / total_hours * 100) if total_hours > 0 else 0
            st.metric("Paid Hours %", f"{paid_ratio:.1f}%")
        with col4:
            approved_ratio = (approved_hours / total_hours * 100) if total_hours > 0 else 0
            st.metric("Approved %", f"{approved_ratio:.1f}%")
        with col5:
            st.metric("Active Users", df['user_name'].nunique())

    def render_analysis_tabs(self, df):
        """Render analysis tabs with improved descriptions"""
        if df.empty:
            st.warning(get_text('messages.no_data', st.session_state.language))
            return

        tabs = st.tabs([
            get_text('charts.cost_distribution.title', st.session_state.language),
            get_text('charts.timeline.title', st.session_state.language),
            get_text('charts.activities.title', st.session_state.language),
            get_text('charts.performance.title', st.session_state.language),
            get_text('charts.kpi.title', st.session_state.language),
            get_text('tabs.raw_data', st.session_state.language)
        ])

        charts = self.viz.create_cost_dashboard(df, self.HOURLY_RATE)
        user_charts = self.viz.create_users_dashboard(df, self.HOURLY_RATE)
        performance_charts = self.viz.create_performance_dashboard(df, self.HOURLY_RATE)
        
        with tabs[0]:
            st.info(get_text('charts.cost_distribution.description', st.session_state.language))
            if 'cost_distribution' in charts:
                st.plotly_chart(charts['cost_distribution'], use_container_width=True)
        
        with tabs[1]:
            st.info(get_text('charts.timeline.description', st.session_state.language))
            if 'timeline' in charts:
                st.plotly_chart(charts['timeline'], use_container_width=True)
        
        with tabs[2]:
            st.info(get_text('charts.activities.description', st.session_state.language))
            if 'activities' in charts:
                st.plotly_chart(charts['activities'], use_container_width=True)
        
        with tabs[3]:
            st.info(get_text('charts.performance.description', st.session_state.language))
            st.plotly_chart(user_charts['performance'], use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_daily_hours = df.groupby('spent_on')['hours'].sum().mean()
                st.metric("Avg Daily Hours", f"{avg_daily_hours:.1f}")
            with col2:
                efficiency_rate = (df['is_approved'] & df['is_paid']).mean() * 100
                st.metric("Efficiency Rate", f"{efficiency_rate:.1f}%")
            with col3:
                productivity_trend = df.groupby('spent_on')['hours'].sum().pct_change().mean() * 100
                st.metric("Productivity Trend", f"{productivity_trend:+.1f}%")

        with tabs[4]:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.info(get_text('charts.kpi.description', st.session_state.language))
            with col2:
                st.plotly_chart(performance_charts['metrics'], use_container_width=True)
            
            st.markdown("""
            ### Key Performance Indicators (KPIs)
            - **CPI (Cost Performance Index)**: Measures cost efficiency. Target = 1.0
                - CPI > 1: Under budget
                - CPI < 1: Over budget
            - **SPI (Schedule Performance Index)**: Measures schedule efficiency. Target = 1.0
                - SPI > 1: Ahead of schedule
                - SPI < 1: Behind schedule
            - **Resource Utilization**: Effective resource usage. Target > 80%
            - **Quality Rate**: Work meeting quality standards. Target > 90%
            """)

        with tabs[5]:
            st.dataframe(df, use_container_width=True)

    def run(self):
        """Run the dashboard with improved error handling"""
        try:
            # Handle authentication
            username = self.auth.login()
            if not username:
                return

            # Get user role safely
            role = st.session_state.get('user_role', '')
            
            # Show localized welcome message
            st.title(get_text('title', st.session_state.get('language', 'en')))
            if username and role:
                st.markdown(f"{get_text('welcome', st.session_state.get('language', 'en'))} **{username}** ({role})")

            # Render language selector first
            self.render_language_selector()
            
            # Add logout button in sidebar
            with st.sidebar:
                st.markdown("---")
                if st.button("Logout"):
                    self.auth.logout()
                    st.rerun()

            try:
                filter_result = self.render_sidebar()
                if filter_result != (None, None, None):
                    start_date, end_date, project_ids = filter_result
                    df = self.load_data(start_date, end_date, project_ids)
                    
                    if not df.empty:
                        # Show single date range at the top
                        min_date = df['spent_on'].min()
                        max_date = df['spent_on'].max()
                        st.markdown(f"**Date Range**: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
                        
                        self.render_metrics(df)
                        if self.auth.check_role_access("admin"):
                            self.render_analysis_tabs(df)
                        else:
                            self.render_limited_analysis(df)
                    else:
                        st.info("No data available for the selected filters.")
                else:
                    st.info("Please select filters and click Apply to view the dashboard.")

            except Exception as e:
                st.error(f"Error loading data: {str(e)}")

        except Exception as e:
            st.error(f"Error running dashboard: {str(e)}")
            if st.session_state.get('authenticated'):
                self.auth.logout()

if __name__ == "__main__":
    app = DashboardApp()
    app.run()