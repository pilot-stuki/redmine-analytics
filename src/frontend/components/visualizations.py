import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Tuple  # Added import for Tuple
import numpy as np

class CostAnalyticsVisualizations:
    """Visualization components for cost analytics dashboard"""
    
    # Enhanced color scheme with better contrast
    COLORS = {
        'status': {
            'Paid & Approved': '#4CAF50',      # Material Green
            'Paid & Not Approved': '#FFC107',   # Material Amber
            'Unpaid & Approved': '#2196F3',    # Material Blue
            'Unpaid & Not Approved': '#F44336' # Material Red
        },
        'background': '#1E1E1E',  # Dark background
        'text': '#FFFFFF',        # White text
        'grid': '#333333',        # Dark grid
        'accent': '#64B5F6'       # Light blue accent
    }

    # Chart template for consistent styling
    CHART_TEMPLATE = dict(
        font=dict(
            family="Arial",
            size=12,
            color=COLORS['text']
        ),
        paper_bgcolor=COLORS['background'],
        plot_bgcolor=COLORS['background'],
        margin=dict(t=50, b=50, l=50, r=50),
        hoverlabel=dict(
            bgcolor='rgba(50, 50, 50, 0.8)',
            font_size=14,
            font_color='white'
        )
    )

    # Updated chart style for dark mode
    CHART_STYLE = dict(
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['background'],
        font=dict(
            size=12,
            color=COLORS['text']
        ),
        hoverlabel=dict(
            bgcolor='rgba(50, 50, 50, 0.8)',
            font_size=14,
            font_color=COLORS['text']
        ),
        margin=dict(t=100, b=100),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(50, 50, 50, 0.8)',
            font=dict(color=COLORS['text'])
        )
    )

    # Updated axis style for dark mode
    AXIS_STYLE = dict(
        gridcolor=COLORS['grid'],
        tickfont=dict(size=12, color=COLORS['text']),
        title_font=dict(size=14, color=COLORS['text']),
        zerolinecolor=COLORS['grid']
    )

    # Enhanced legend layout
    LEGEND_LAYOUT = dict(
        orientation="h",
        yanchor="bottom",
        y=-0.25,
        xanchor="center",
        x=0.5,
        bgcolor="rgba(255, 255, 255, 0.95)",
        bordercolor="rgba(0,0,0,0.2)",
        borderwidth=1,
        font=dict(size=12)
    )

    @staticmethod
    def create_project_selector(projects, chart_name=""):
        """Create project selector dropdown menu"""
        return [{
            'buttons': [
                {
                    'label': 'All Projects',
                    'method': 'update',
                    'args': [{'visible': [True] * (len(projects) + (1 if chart_name == 'users' else 0))}]
                }
            ] + [
                {
                    'label': project,
                    'method': 'update',
                    'args': [{
                        'visible': [p == project for p in projects] + 
                                 ([True] if chart_name == 'users' else [])
                    }]
                } for project in projects
            ],
            'direction': 'down',
            'showactive': True,
            'x': 0.1,
            'y': 1.15
        }]

    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, str]:
        """Validate DataFrame has required columns and correct data types"""
        required_columns = {
            'hours': 'numeric',
            'is_approved': 'boolean',
            'is_paid': 'boolean',
            'project_name': 'object',
            'spent_on': 'datetime',
            'user_name': 'object',
            'activity_name': 'object'
        }
        missing_columns = [col for col in required_columns.keys() if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
        try:
            if not pd.api.types.is_numeric_dtype(df['hours']):
                df['hours'] = pd.to_numeric(df['hours'], errors='coerce').fillna(0)
            for col in ['is_approved', 'is_paid']:
                if not pd.api.types.is_bool_dtype(df[col]):
                    df[col] = df[col].astype(bool)
            if not pd.api.types.is_datetime64_any_dtype(df['spent_on']):
                df['spent_on'] = pd.to_datetime(df['spent_on'])
            return True, "Validation successful"
        except Exception as e:
            return False, f"Error validating data types: {str(e)}"

    @staticmethod
    def create_cost_dashboard(df: pd.DataFrame, hourly_rate: float = 1650) -> Dict[str, go.Figure]:
        """Create dashboard charts with improved styling"""
        if df.empty:
            return {}
        
        # Ensure we have unique entries for calculations
        df = df.drop_duplicates(subset=['id'])
        
        # Pre-calculate status totals
        status_combinations = [
            ('Paid & Approved', df['is_paid'] & df['is_approved']),
            ('Paid & Not Approved', df['is_paid'] & ~df['is_approved']),
            ('Unpaid & Approved', ~df['is_paid'] & df['is_approved']),
            ('Unpaid & Not Approved', ~df['is_paid'] & ~df['is_approved'])
        ]

        status_data = {
            status: df[mask]['hours'].sum()
            for status, mask in status_combinations
        }
        
        charts = {}

        # 1. Cost Distribution Chart
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "table", "colspan": 2}, None]],
            column_widths=[0.4, 0.6],
            row_heights=[0.7, 0.3],
            subplot_titles=("<b>Status Distribution</b>", "<b>Project Costs</b>")
        )
        
        # Pie chart: Convert hours to cost and use new color scheme
        values = [v * hourly_rate for v in status_data.values()]
        fig.add_trace(
            go.Pie(
                labels=list(status_data.keys()),
                values=values,
                hole=0.4,
                marker=dict(colors=list(CostAnalyticsVisualizations.COLORS['status'].values())),
                textinfo='label+percent',
                textposition='outside',
                hovertemplate="<b>%{label}</b><br>Cost: ₽%{value:,.0f}<br>Hours: %{customdata:.1f}<extra></extra>",
                customdata=list(status_data.values())
            ),
            row=1, col=1
        )
        
        # Stacked bar chart for projects
        project_data = df.groupby(['project_name', 'is_paid', 'is_approved']).agg({'hours': 'sum'}).reset_index()
        for status, conditions in [
            ('Paid & Approved', (True, True)),
            ('Paid & Not Approved', (True, False)),
            ('Unpaid & Approved', (False, True)),
            ('Unpaid & Not Approved', (False, False))
        ]:
            mask = (project_data['is_paid'] == conditions[0]) & (project_data['is_approved'] == conditions[1])
            data = project_data[mask]
            if not data.empty:
                fig.add_trace(
                    go.Bar(
                        name=f"{status} (Cost)",
                        x=data['project_name'],
                        y=data['hours'] * hourly_rate,
                        marker_color=CostAnalyticsVisualizations.COLORS['status'][status],
                        text=data.apply(lambda x: f"₽{x['hours'] * hourly_rate:,.0f}<br>{x['hours']:.1f}h", axis=1),
                        textposition='auto',
                        hovertemplate="<b>%{x}</b><br>Status: " + status +
                                      "<br>Cost: ₽%{y:,.0f}<br>Hours: %{customdata:.1f}<extra></extra>",
                        customdata=data['hours']
                    ),
                    row=1, col=2
                )
        
        # Metrics table without duplicate values
        table_data = []
        for status, hours in status_data.items():
            cost = hours * hourly_rate
            table_data.append([f"<b>{status}</b>", f"{hours:.1f}", f"₽{cost:,.0f}"])
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['<b>Status</b>', '<b>Hours</b>', '<b>Cost (RUB)</b>'],
                    font=dict(size=13, color='white'),
                    fill_color='#1a237e',
                    align='left',
                    height=35
                ),
                cells=dict(
                    values=list(zip(*table_data)),
                    font=dict(size=12),
                    fill_color='rgba(50, 50, 50, 0.8)',
                    align='left',
                    height=30
                )
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            **CostAnalyticsVisualizations.CHART_TEMPLATE,
            showlegend=True,
            barmode='stack',
            height=800,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, bgcolor='rgba(50, 50, 50, 0.8)'),
            yaxis2=dict(title="Cost (RUB)", tickformat="₽,.0f", gridcolor=CostAnalyticsVisualizations.COLORS['grid'])
        )
        
        fig = CostAnalyticsVisualizations.add_legend_controls(fig)
        charts['cost_distribution'] = fig

        # 2. Timeline Chart: Daily costs by project
        timeline_data = df.groupby(['spent_on', 'project_name'])['hours'].sum().reset_index()
        timeline_data['cost'] = timeline_data['hours'] * hourly_rate
        fig = go.Figure()
        for project in df['project_name'].unique():
            proj = timeline_data[timeline_data['project_name'] == project]
            if not proj.empty:
                fig.add_trace(
                    go.Scatter(
                        x=proj['spent_on'],
                        y=proj['cost'],
                        name=project,
                        mode='lines+markers',
                        hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Project: " + project +
                                      "<br>Cost: ₽%{y:,.0f}<br>Hours: %{customdata:.1f}<extra></extra>",
                        customdata=proj['hours']
                    )
                )
        fig.update_layout(
            title="<b>Daily Costs by Project</b>",
            xaxis=dict(title="Date", **CostAnalyticsVisualizations.AXIS_STYLE),
            yaxis=dict(title="Cost (RUB)", tickformat="₽,.0f", **CostAnalyticsVisualizations.AXIS_STYLE),
            hovermode='x unified',
            **CostAnalyticsVisualizations.CHART_TEMPLATE
        )
        fig = CostAnalyticsVisualizations.add_legend_controls(fig)
        charts['timeline'] = fig

        # 3. Activities Chart: Costs by activity
        activity_data = df.groupby(['activity_name', 'project_name'])['hours'].sum().reset_index()
        activity_data['cost'] = activity_data['hours'] * hourly_rate
        fig = go.Figure()
        for project in df['project_name'].unique():
            proj = activity_data[activity_data['project_name'] == project]
            if not proj.empty:
                fig.add_trace(
                    go.Bar(
                        name=project,
                        x=proj['activity_name'],
                        y=proj['cost'],
                        hovertemplate="<b>%{x}</b><br>Project: " + project +
                                      "<br>Cost: ₽%{y:,.0f}<br>Hours: %{customdata:.1f}<extra></extra>",
                        customdata=proj['hours']
                    )
                )
        fig.update_layout(
            title="<b>Costs by Activity</b>",
            xaxis=dict(title="Activity", **CostAnalyticsVisualizations.AXIS_STYLE),
            yaxis=dict(title="Cost (RUB)", tickformat="₽,.0f", **CostAnalyticsVisualizations.AXIS_STYLE),
            barmode='group',
            **CostAnalyticsVisualizations.CHART_TEMPLATE
        )
        fig = CostAnalyticsVisualizations.add_legend_controls(fig)
        charts['activities'] = fig
        
        # 4. Users Chart: Costs by user and payment rate line
        user_data = df.groupby(['user_name', 'project_name'])['hours'].sum().reset_index()
        user_data['cost'] = user_data['hours'] * hourly_rate
        fig = go.Figure()
        for project in df['project_name'].unique():
            proj = user_data[user_data['project_name'] == project]
            if not proj.empty:
                fig.add_trace(
                    go.Bar(
                        name=project,
                        x=proj['user_name'],
                        y=proj['cost'],
                        hovertemplate="<b>%{x}</b><br>Project: " + project +
                                      "<br>Cost: ₽%{y:,.0f}<br>Hours: %{customdata:.1f}<extra></extra>",
                        customdata=proj['hours']
                    )
                )
        user_payment_rates = df.groupby('user_name')['is_paid'].mean() * 100
        fig.add_trace(
            go.Scatter(
                x=user_payment_rates.index,
                y=user_payment_rates.values,
                name='Payment Rate',
                yaxis='y2',
                line=dict(color='red', width=2),
                mode='lines+markers'
            )
        )
        fig.update_layout(
            title="<b>Costs by User</b>",
            xaxis=dict(title="User", **CostAnalyticsVisualizations.AXIS_STYLE),
            yaxis=dict(title="Cost (RUB)", tickformat="₽,.0f", **CostAnalyticsVisualizations.AXIS_STYLE),
            yaxis2=dict(title="Payment Rate (%)", overlaying='y', side='right', range=[0, 100], **CostAnalyticsVisualizations.AXIS_STYLE),
            barmode='group',
            **CostAnalyticsVisualizations.CHART_TEMPLATE
        )
        fig = CostAnalyticsVisualizations.add_legend_controls(fig)
        charts['users'] = fig

        return charts

    def create_detailed_user_performance(self, df: pd.DataFrame, hourly_rate: float = 1650) -> go.Figure:
        """Create detailed user performance analysis with unique aggregations"""
        df['spent_on'] = pd.to_datetime(df['spent_on']).dt.date
        
        # First group by user and project
        user_project_metrics = (df.groupby(['user_name', 'project_name'])
                                .agg({
                                    'hours': 'sum',
                                    'is_paid': 'mean',
                                    'is_approved': 'mean',
                                    'spent_on': ['min', 'max']
                                })
                                .reset_index())
        
        # Then aggregate to user level
        user_metrics = (user_project_metrics.groupby('user_name')
                                         .agg({
                                             'hours': 'sum',
                                             'is_paid': 'mean',
                                             'is_approved': 'mean',
                                             'project_name': 'nunique',
                                             'spent_on': ['min', 'max']
                                         })
                                         .reset_index())
        
        user_metrics['cost'] = user_metrics['hours'] * hourly_rate
        user_metrics['projects_count'] = user_metrics['project_name']
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Cost by User",
                "Payment & Approval Rates",
                "Projects per User",
                "Hours Distribution"
            )
        )
        
        # Cost by User
        fig.add_trace(
            go.Bar(
                x=user_metrics['user_name'],
                y=user_metrics['cost'],
                name="Total Cost"
            ),
            row=1, col=1
        )
        
        # Payment & Approval Rates
        fig.add_trace(
            go.Scatter(
                x=user_metrics['user_name'],
                y=user_metrics['is_paid'] * 100,
                name="Payment Rate",
                mode='lines+markers'
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Scatter(
                x=user_metrics['user_name'],
                y=user_metrics['is_approved'] * 100,
                name="Approval Rate",
                mode='lines+markers'
            ),
            row=1, col=2
        )
        
        # Projects per User
        fig.add_trace(
            go.Bar(
                x=user_metrics['user_name'],
                y=user_metrics['projects_count'],
                name="Project Count"
            ),
            row=2, col=1
        )
        
        # Hours Distribution
        fig.add_trace(
            go.Box(
                x=df['user_name'],
                y=df['hours'],
                name="Hours Distribution"
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="User Performance Analysis",
            title_x=0.5,
            **CostAnalyticsVisualizations.CHART_TEMPLATE
        )
        
        return fig

    def create_performance_dashboard(self, df: pd.DataFrame, hourly_rate: float = 1650) -> Dict[str, go.Figure]:
        """Create performance analytics dashboard with industry standard metrics"""
        if df.empty:
            return {}

        # Calculate KPIs
        metrics = {
            'cpi': (df['is_approved'] & df['is_paid']).mean() * 100,
            'spi': (df.groupby('spent_on')['hours'].sum().pct_change().mean() + 1) * 100,
            'utilization': (len(df[df['hours'] > 0]) / len(df) if len(df) > 0 else 0) * 100,
            'quality': df['is_approved'].mean() * 100
        }

        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{"type": "indicator"}, {"type": "indicator"}],
                  [{"type": "indicator"}, {"type": "indicator"}]],
            subplot_titles=(
                "Cost Performance Index (CPI)",
                "Schedule Performance Index (SPI)",
                "Resource Utilization",
                "Quality Rate"
            )
        )

        # Add KPI indicators
        kpi_configs = [
            ('cpi', [0, 200], 100),
            ('spi', [0, 200], 100),
            ('utilization', [0, 100], 80),
            ('quality', [0, 100], 90)
        ]

        for idx, (metric, range_vals, target) in enumerate(kpi_configs):
            row = (idx // 2) + 1
            col = (idx % 2) + 1
            
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=metrics[metric],
                    delta={'reference': target},
                    gauge={
                        'axis': {'range': range_vals},
                        'steps': [
                            {'range': [range_vals[0], target*0.8], 'color': 'red'},
                            {'range': [target*0.8, target*1.2], 'color': 'green'},
                            {'range': [target*1.2, range_vals[1]], 'color': 'yellow'}
                        ],
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': target
                        }
                    }
                ),
                row=row, col=col
            )

        fig.update_layout(
            height=800,
            **CostAnalyticsVisualizations.CHART_TEMPLATE
        )

        return {'metrics': fig}

    @staticmethod
    def add_legend_controls(fig: go.Figure) -> go.Figure:
        """Simplified legend controls"""
        # Remove the method as we're not using custom legend controls anymore
        return fig

    @staticmethod
    def format_percentage(value: float) -> str:
        """Format value as percentage with 1 decimal place"""
        return f"{value:.1f}%"

    @staticmethod
    def create_users_dashboard(df: pd.DataFrame, hourly_rate: float = 1650) -> Dict[str, go.Figure]:
        """Create separate visualizations for user performance"""
        user_totals = df.groupby('user_name').agg({
            'hours': 'sum',
            'is_paid': 'mean',
            'is_approved': 'mean'
        }).reset_index()
        
        # Convert rates to percentages
        user_totals['is_paid'] = user_totals['is_paid'] * 100
        user_totals['is_approved'] = user_totals['is_approved'] * 100
        user_totals['cost'] = user_totals['hours'] * hourly_rate

        # Create user metrics visualization with percentage formatting
        fig = go.Figure()
        
        # Add cost bars with percentage annotations
        fig.add_trace(
            go.Bar(
                name="Total Cost",
                x=user_totals['user_name'],
                y=user_totals['cost'],
                text=[f"₽{cost:,.0f}<br>{hours:.1f}h" for cost, hours in zip(user_totals['cost'], user_totals['hours'])],
                textposition='auto',
                marker_color=CostAnalyticsVisualizations.COLORS['accent']
            )
        )

        # Add payment and approval rates with percentage formatting
        fig.add_trace(
            go.Scatter(
                name="Payment Rate",
                x=user_totals['user_name'],
                y=user_totals['is_paid'],
                mode='markers+lines+text',
                text=[f"{x:.1f}%" for x in user_totals['is_paid']],
                textposition='top center',
                yaxis='y2',
                marker=dict(size=12),
                line=dict(width=2),
                marker_color=CostAnalyticsVisualizations.COLORS['status']['Paid & Approved']
            )
        )

        fig.add_trace(
            go.Scatter(
                name="Approval Rate",
                x=user_totals['user_name'],
                y=user_totals['is_approved'],
                mode='markers+lines+text',
                text=[f"{x:.1f}%" for x in user_totals['is_approved']],
                textposition='bottom center',
                yaxis='y2',
                marker=dict(size=12),
                line=dict(width=2, dash='dot'),
                marker_color=CostAnalyticsVisualizations.COLORS['status']['Unpaid & Approved']
            )
        )

        fig.update_layout(
            title="<b>User Performance Overview</b>",
            yaxis=dict(
                title="Cost (RUB)",
                tickformat="₽,.0f",
                **CostAnalyticsVisualizations.AXIS_STYLE
            ),
            yaxis2=dict(
                title="Rate (%)",
                overlaying='y',
                side='right',
                range=[0, 100],
                **CostAnalyticsVisualizations.AXIS_STYLE
            ),
            **CostAnalyticsVisualizations.CHART_TEMPLATE
        )

        fig = CostAnalyticsVisualizations.add_legend_controls(fig)
        return {'performance': fig}

    @staticmethod
    def ensure_array_dimensions(df: pd.DataFrame, dimension: str, values: list) -> pd.DataFrame:
        """Ensure consistent dimensions across aggregations"""
        unique_values = df[dimension].unique()
        missing_values = set(unique_values) - set(values)
        
        if missing_values:
            # Add missing values with zeros
            for value in missing_values:
                values.append(value)
        
        return values