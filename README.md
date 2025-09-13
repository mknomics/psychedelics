# Erowid Experience Reports Scraper

A production-quality Python scraper for extracting user experience reports from Erowid.org. This tool systematically collects experience reports from three specific substance categories and exports them to a structured CSV format.

## Features

- **Comprehensive Data Extraction**: Scrapes experience reports including narratives, dosage information, user demographics, and metadata
- **Pagination Support**: Automatically detects and processes all available pages for each substance category
- **Robust Error Handling**: Includes retry logic, timeout handling, and graceful error recovery
- **Polite Scraping**: Implements delays between requests to avoid overwhelming the server
- **Progress Tracking**: Visual progress bars show scraping status
- **Structured Output**: Exports data to CSV with 42 standardized columns

## Data Collected

The scraper extracts the following information from each experience report:

### Basic Information
- Title, Author, Experience Rating
- Publication Date, Experience Date
- Gender, Age at Experience
- Body Weight (value and unit)
- View Count, Report ID

### Dosage Information
- Up to 10 substances with:
  - Substance name
  - Dose amount
  - Administration method

### Narrative
- Full experience report text

## Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Setup

1. Clone or download this project

2. Create a virtual environment:
```bash
python3 -m venv webscraping_env
source webscraping_env/bin/activate  # On Windows: webscraping_env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the full scraper to collect all available experiences:
```bash
python erowid_scraper.py
```

**Note**: Full scraping will collect approximately 6,200 experiences and may take 5-6 hours to complete.

### Test Mode

To test with a limited number of experiences per page:
```bash
python erowid_scraper.py 5  # Scrapes only 5 experiences per page
```

This is useful for testing the scraper functionality without waiting for the full dataset.

## Output

The scraper creates a file named `erowid_experiences.csv` with 42 columns:

### Column Structure
```
title, author, date_experience, date_published, gender, age_experience, 
experience_rating, weight_val, weight_scale, text, id, number_views,
substance_1, dose_1, method_1, ..., substance_10, dose_10, method_10
```

### Data Types
- **Dates**: datetime format (pandas datetime64)
- **Numeric**: id (int), number_views (int), weight_val (float)
- **Text**: All other fields as strings

## Scope

The scraper targets three specific substance categories identified by their Erowid IDs:
- **S1=39**: ~3,400 experiences (34 pages)
- **S1=2**: ~2,600 experiences (27 pages)
- **S1=8**: ~200 experiences (2 pages)

Total: Approximately 6,200 experience reports

## Technical Details

### Pagination
The scraper automatically:
1. Detects the total number of pages for each substance
2. Iterates through all pages using URL parameters (Start=0, Start=100, etc.)
3. Processes 100 experiences per page

### Rate Limiting
- Random delay of 1-3 seconds between requests
- HTTP retry adapter with exponential backoff
- Timeout of 30 seconds per request

### SSL Handling
The scraper disables SSL verification for Erowid due to certificate issues. This is acceptable for public data scraping but should not be used for sensitive applications.

## Error Handling

The scraper includes robust error handling:
- Retries failed requests up to 3 times
- Continues scraping even if individual detail pages fail
- Logs all errors for debugging
- Saves partial data even if some fields are missing

## Logging

The scraper provides detailed logging including:
- Progress updates for each page and substance
- Error messages for failed requests
- Summary statistics upon completion

## Dependencies

- **requests**: HTTP library for web requests
- **beautifulsoup4**: HTML parsing and data extraction
- **lxml**: Fast XML/HTML parser backend
- **pandas**: Data manipulation and CSV export
- **python-dateutil**: Flexible date parsing
- **tqdm**: Progress bar visualization

## Ethical Considerations

This scraper:
- Respects server resources with rate limiting
- Only accesses publicly available data
- Does not require authentication
- Implements polite scraping practices

## Troubleshooting

### SSL Certificate Errors
The scraper automatically handles Erowid's SSL certificate issues. No manual intervention needed.

### Memory Issues
For systems with limited memory, consider:
- Running the scraper with smaller batches using the limit parameter
- Processing one substance at a time by modifying the listing_urls in the script

### Incomplete Data
If the scraper is interrupted:
- The CSV file will contain all successfully scraped experiences up to that point
- You can modify the script to resume from a specific page if needed

## License

This scraper is provided for educational and research purposes. Please respect Erowid's terms of service and use the data responsibly.

## Support

For issues or questions about the scraper, please refer to the inline documentation in `erowid_scraper.py`.