TRANSLATIONS = {
    'en': {
        'title': 'Labor Cost Analytics Dashboard',
        'welcome': 'Welcome',
        'filters': {
            'header': 'Filters',
            'date_range': 'Date Range',
            'select_range': 'Select time range',
            'end_date': 'End date',
            'start_date': 'Start date',
            'project_filter': 'Project Filter',
            'select_projects': 'Select Projects',
            'apply': 'Apply Filters'
        },
        'date_ranges': {
            'last_7': 'Last 7 days',
            'last_30': 'Last 30 days',
            'last_quarter': 'Last Quarter',
            'this_year': 'This Year',
            'custom': 'Custom'
        },
        'metrics': {
            'total_hours': 'Total Hours',
            'total_cost': 'Total Cost (RUB)',
            'paid_hours': 'Paid Hours %',
            'approved': 'Approved %',
            'active_users': 'Active Users',
            'avg_daily_hours': 'Avg Daily Hours',
            'efficiency_rate': 'Efficiency Rate',
            'productivity_trend': 'Productivity Trend'
        },
        'tabs': {
            'cost_distribution': 'Cost Distribution',
            'timeline': 'Timeline',
            'activities': 'Activities',
            'users_performance': 'Users & Performance',
            'project_kpis': 'Project KPIs',
            'raw_data': 'Raw Data'
        },
        'messages': {
            'no_data': 'No data available for the selected filters.',
            'select_filters': 'Please select filters and click Apply to view the dashboard.'
        },
        'charts': {
            'cost_distribution': {
                'title': 'Cost Distribution',
                'description': 'Distribution of costs by payment status and project allocation.'
            },
            'timeline': {
                'title': 'Timeline',
                'description': 'Cost and hours trends over time. Shows resource utilization patterns.'
            },
            'activities': {
                'title': 'Activities',
                'description': 'Distribution of work by activity type.'
            },
            'performance': {
                'title': 'Performance',
                'description': 'Team efficiency and productivity indicators.'
            },
            'kpi': {
                'title': 'KPIs',
                'description': 'Project health metrics: cost efficiency, schedule adherence, and quality.'
            }
        }
    },
    'ru': {
        'title': 'Панель аналитики трудозатрат',
        'welcome': 'Добро пожаловать',
        'filters': {
            'header': 'Фильтры',
            'date_range': 'Период',
            'select_range': 'Выберите период',
            'end_date': 'Дата окончания',
            'start_date': 'Дата начала',
            'project_filter': 'Фильтр проектов',
            'select_projects': 'Выберите проекты',
            'apply': 'Применить фильтры'
        },
        'date_ranges': {
            'last_7': 'Последние 7 дней',
            'last_30': 'Последние 30 дней',
            'last_quarter': 'Последний квартал',
            'this_year': 'Этот год',
            'custom': 'Произвольный'
        },
        'metrics': {
            'total_hours': 'Всего часов',
            'total_cost': 'Общая стоимость (РУБ)',
            'paid_hours': 'Оплачено %',
            'approved': 'Согласовано %',
            'active_users': 'Активные пользователи',
            'avg_daily_hours': 'Ср. часов в день',
            'efficiency_rate': 'Эффективность',
            'productivity_trend': 'Тренд продуктивности'
        },
        'tabs': {
            'cost_distribution': 'Распределение затрат',
            'timeline': 'График по времени',
            'activities': 'Активности',
            'users_performance': 'Показатели пользователей',
            'project_kpis': 'KPI проектов',
            'raw_data': 'Исходные данные'
        },
        'messages': {
            'no_data': 'Нет данных для выбранных фильтров.',
            'select_filters': 'Пожалуйста, выберите фильтры и нажмите Применить для просмотра данных.'
        },
        'charts': {
            'cost_distribution': {
                'title': 'Распределение затрат',
                'description': 'Распределение затрат по статусам оплаты и проектам.'
            },
            'timeline': {
                'title': 'График по времени',
                'description': 'Динамика затрат и часов. Показывает паттерны использования ресурсов.'
            },
            'activities': {
                'title': 'Активности',
                'description': 'Распределение работы по типам активности.'
            },
            'performance': {
                'title': 'Эффективность',
                'description': 'Показатели эффективности и продуктивности команды.'
            },
            'kpi': {
                'title': 'KPI',
                'description': 'Метрики проекта: эффективность затрат, соблюдение сроков и качество.'
            }
        }
    }
}

def get_text(key: str, lang: str = 'en') -> str:
    """Get translated text by key"""
    keys = key.split('.')
    current = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    for k in keys:
        if isinstance(current, dict):
            current = current.get(k, k)
        else:
            return k
    return current
