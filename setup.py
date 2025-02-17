from setuptools import setup, find_packages

setup(
    name="redmine_app",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        'streamlit>=1.32.0',
        'pandas>=2.2.0',
        'numpy>=1.26.0',
        'requests>=2.31.0',
        'plotly>=5.18.0',
        'python-dotenv>=1.0.0',
        'openai>=1.12.0',
        'xlsxwriter>=3.1.9',
        'pytest>=8.0.0',
        'python-dateutil>=2.8.2'
    ],
    extras_require={
        'dev': [
            'pytest>=8.0.0',
            'pytest-cov>=4.1.0',
        ],
    }
)