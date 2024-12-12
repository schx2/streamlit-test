# Plumber Audience Analysis

A Streamlit application for analyzing property and permit data to identify plumbing-related patterns and insights.

## Features

- Property and permit data visualization
- Filtering by various property attributes
- Time-based analysis of permits relative to property sales
- Interactive charts and statistics

## Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd myPlumberAudience
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Data Files:
Place your property-permit match files in the root directory with the naming convention `[STATE]_matches.json` (e.g., `MD_matches.json`, `VA_matches.json`).

## Running the Application

1. Start the Streamlit server:
```bash
streamlit run streamlit_app.py
```

2. Open your browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

## Deployment

This application can be deployed on Streamlit Cloud:

1. Push your code to a GitHub repository
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Deploy the application

## File Structure

- `streamlit_app.py`: Main application file
- `audienceBuilder.py`: Core data processing logic
- `filters.py`: Filter components and logic
- `utils.py`: Utility functions and visualizations
- `joinPermitsRentcast.py`: Data joining and processing script

## Data Requirements

The application expects JSON files containing property and permit data with the following structure:
- Property data: id, address, city, state, lastSaleDate, lastSalePrice, etc.
- Permit data: permit_id, file_date, description, etc.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 