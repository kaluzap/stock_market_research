# Stock Market Research

This tool provides a report on stock market data using `yfinance`.

## How to use

### 1. Installation

Ensure you have the required dependencies:

```bash
pip install -r requirements.txt
```

### 2. Generate Report (CLI)

To generate the report once from the terminal:

```bash
# Basic report
python create_report.py -d my_data/

# Report with data actualization (downloads new data)
python create_report.py -d my_data/ -a
```

### 3. Web Dashboard (Recommended)

To run a web server that allows viewing and updating the report from the browser:

```bash
python server.py
```

- **View Report:** Open `http://localhost:5000` in your browser.
- **Actualize Data:** Click the **"Actualize Data"** button in the header to download the latest stock information and refresh the page.

## File Structure

- `create_report.py`: Main script to generate the HTML report.
- `server.py`: Flask server to host the dashboard.
- `configuration.py`: Project settings and data configurations.
- `my_data/`: Directory containing stock lists and configurations.
- `reports/`: Location of generated HTML reports.
- `utils/`: Data processing utilities.
