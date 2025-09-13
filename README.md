# Erowid Experience Reports Scraper

A production-quality Python scraper for extracting user experience reports from Erowid.org with comprehensive progress tracking and resume capabilities. This tool systematically collects experience reports from three specific substance categories and exports them to a structured CSV format.

## ✨ Key Features

- **🔄 Resume Capability**: Automatically saves progress and resumes from interruptions
- **📊 Comprehensive Data**: Scrapes 42+ data fields including narratives, dosage, demographics
- **📖 Full Pagination**: Processes all available pages (~6,200 total experiences)  
- **🛡️ Robust Error Handling**: Retry logic, timeout handling, graceful failure recovery
- **🎯 Polite Scraping**: Rate limiting with 1-3 second delays between requests
- **📈 Progress Tracking**: Visual progress bars and detailed logging
- **📁 Structured Export**: Clean CSV output with standardized 42-column schema

## 📋 Data Collected

### Basic Information (12 fields)
- **Report Details**: Title, Author, Experience Rating, Report ID, View Count
- **Timing**: Publication Date, Experience Date  
- **Demographics**: Gender, Age at Experience
- **Physical**: Body Weight (numeric value + unit)
- **Content**: Full experience narrative text

### Dosage Information (30 fields)
For up to 10 substances per report:
- **Substance**: Name/type (e.g., "LSD", "Psilocybe cubensis")
- **Dose**: Amount (e.g., "100 μg", "3.5 g")  
- **Method**: Administration route (e.g., "oral", "insufflated")

## 🚀 Quick Start

### Prerequisites
- **Python**: 3.11 or higher
- **Platform**: Windows, macOS, or Linux
- **Memory**: 2GB+ RAM recommended for full dataset

### Installation

1. **Download/Clone** this project to your local machine

2. **Create Virtual Environment**:
```bash
python3 -m venv webscraping_env
source webscraping_env/bin/activate  # Linux/Mac
# OR
webscraping_env\Scripts\activate     # Windows
```

3. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

## 📖 Usage Guide

### Full Scraping (Recommended)
```bash
python erowid_scraper.py
```
- Scrapes **~6,200 experiences** across all pages
- **Duration**: 5-6 hours (depends on network speed)
- **Resumable**: If interrupted, simply run again to continue

### Resume from Interruption
```bash
python erowid_scraper.py
```
If scraping was interrupted, the script will automatically:
- ✅ Load previous progress from `scraping_progress.json`
- ✅ Skip already-completed pages
- ✅ Continue from where it left off
- ✅ Show detailed resume information

### Start Fresh (Clear Progress)
```bash
python erowid_scraper.py --clear-progress
```
Forces a fresh start by clearing all previous progress.

### Test Mode
```bash
python erowid_scraper.py 5
```
Limits scraping to 5 experiences per page for testing (processes 2 pages per substance).

### Test with Fresh Start
```bash
python erowid_scraper.py 5 --clear-progress
```

## 📁 Output Files

### `erowid_experiences.csv`
Main output file with **42 columns** in exact order:
```
title, author, date_experience, date_published, gender, age_experience, 
experience_rating, weight_val, weight_scale, text, id, number_views,
substance_1, dose_1, method_1, substance_2, dose_2, method_2, ...,
substance_10, dose_10, method_10
```

### `scraping_progress.json`
Progress tracking file containing:
- Session timestamps and completion status
- List of completed pages per substance  
- Total experiences scraped
- Individual experience IDs (prevents duplicates)

**Example**:
```json
{
  "session_start": "2025-09-13T12:22:14.038587",
  "last_updated": "2025-09-13T12:22:36.716796",
  "completed_pages": ["39_page_1", "39_page_2", "2_page_1"],
  "total_scraped": 150,
  "substance_progress": {
    "39": {"completed_pages": 15, "experiences_scraped": 1500},
    "2": {"completed_pages": 12, "experiences_scraped": 1200}
  }
}
```

## 🎯 Data Scope

The scraper targets three Erowid substance categories:

| Substance ID | Pages | Experiences | Est. Duration |
|--------------|-------|-------------|---------------|
| **S1=39**    | 34    | ~3,400      | 3-4 hours     |
| **S1=2**     | 27    | ~2,700      | 2-3 hours     |
| **S1=8**     | 2     | ~200        | 10-15 minutes |
| **Total**    | **63**| **~6,300**  | **5-6 hours** |

## 🔧 Technical Implementation

### Data Processing Pipeline
1. **Page Discovery**: Detects total pages per substance via pagination analysis
2. **Listing Extraction**: Parses experience tables to get basic info + detail URLs
3. **Detail Scraping**: Fetches individual experience pages for full data
4. **Data Cleaning**: Type conversion, date parsing, weight normalization
5. **Progress Tracking**: Saves checkpoint after each completed page
6. **CSV Export**: Structured output with proper encoding

### Rate Limiting & Politeness
- **Request Delay**: Random 1-3 seconds between requests
- **Retry Logic**: 3 attempts with exponential backoff
- **Timeout**: 30-second limit per request
- **SSL Handling**: Graceful handling of Erowid's certificate issues
- **User Agent**: Desktop browser identification

### Error Recovery
- **Page-Level**: Continues if individual pages fail
- **Experience-Level**: Saves partial data for failed detail extractions  
- **Session-Level**: Resumable via progress file
- **Logging**: Detailed error tracking for debugging

## 🔍 Data Quality & Types

### Parsed Data Types
- **Dates**: `datetime64[ns]` (pandas datetime)
- **Numeric**: `int64` (id, views), `float64` (weight_val)
- **Text**: `object` (all string fields, nullable)

### Data Completeness
- **Guaranteed Fields**: title, author (from listing pages)
- **Best-Effort Fields**: All detail page fields (may be None if parsing fails)
- **Validation**: Automatic type checking and missing field reporting

## 🛠️ Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| **requests** | 2.32.5 | HTTP client with retry support |
| **beautifulsoup4** | 4.13.5 | HTML parsing and data extraction |  
| **pandas** | 2.3.2 | Data manipulation and CSV export |
| **lxml** | 6.0.1 | Fast XML/HTML parser backend |
| **python-dateutil** | 2.9.0+ | Flexible date parsing |
| **tqdm** | 4.67.1 | Progress bars and status display |
| **urllib3** | 2.5.0+ | HTTP connection pooling |

## 🚨 Troubleshooting

### Common Issues

**Q: Script stops with SSL errors**  
**A**: This is automatically handled. The script disables SSL verification for Erowid.

**Q: Script seems stuck or slow**  
**A**: This is normal. Each page takes ~2-3 seconds due to polite rate limiting.

**Q: I need to stop and resume later**  
**A**: Just Ctrl+C to stop, then run `python erowid_scraper.py` to resume.

**Q: Want to start over completely**  
**A**: Use `python erowid_scraper.py --clear-progress`

**Q: Memory issues on large dataset**  
**A**: The script processes data incrementally, but if issues persist, try processing with limits first.

**Q: Some experiences have missing fields**  
**A**: This is normal. Not all experience reports have complete information (e.g., missing dose charts).

### Resume Verification

When resuming, look for log messages like:
```
INFO - Resuming previous session:
INFO -   Completed pages: 15
INFO -   Experiences scraped: 1500  
INFO - Skipping S1=39 page 1/34 - already completed
```

## ⚖️ Ethical Usage

This scraper follows ethical practices:
- ✅ **Public Data Only**: Scrapes publicly accessible experience reports
- ✅ **Rate Limited**: Respectful delays to avoid server overload  
- ✅ **No Authentication**: Does not bypass any access controls
- ✅ **Educational Purpose**: Intended for research and analysis

**Please**: Respect Erowid's terms of service and use the data responsibly for legitimate research purposes.

## 📞 Support

- **Documentation**: Complete inline code documentation in `erowid_scraper.py`
- **Logging**: Detailed console output shows progress and any issues
- **Progress File**: Check `scraping_progress.json` for session details
- **CSV Validation**: Script reports data completeness and column structure

## 🎯 Perfect For

- **Researchers**: Studying substance experience patterns
- **Data Scientists**: Large-scale text analysis of trip reports  
- **Academic Studies**: Quantitative analysis of psychoactive experiences
- **Personal Projects**: Building datasets for machine learning applications

**Start your comprehensive Erowid data collection today!** 🚀