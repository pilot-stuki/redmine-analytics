# Redmine Analytics Dashboard

A Streamlit-based analytics dashboard for Redmine time tracking data.

## Features

- Time tracking analytics and visualization
- Project cost analysis
- Multi-language support (English/Russian)
- Custom date range filtering
- Project-based filtering
- Interactive visualizations
- Role-based access control

## Setup

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/pilot-stuki/redmine-analytics.git
cd redmine-analytics
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Redmine credentials:
```env
REDMINE_URL=your_redmine_url
REDMINE_API_KEY=your_api_key
```

5. Run the app:
```bash
streamlit run src/frontend/app.py
```

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t redmine-analytics .
```

2. Run the container:
```bash
docker run -p 8501:8501 --env-file .env redmine-analytics
```

Or using docker-compose:
```bash
docker-compose up
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.