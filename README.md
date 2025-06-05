# 🛍️ Etsy Shop Data Scraper

A comprehensive Python-based web scraper designed to extract shop information from Etsy, including sales data, contact information, and revenue analytics through the EverBee API integration.

## ✨ Features

- 🌐 **Multi-Platform Contact Scraping**: Extracts contact information from Instagram, Facebook, Pinterest, Twitter/X, and general websites
- 📊 **EverBee API Integration**: Retrieves average product prices and monthly revenue data
- 🎯 **Intelligent Filtering**: Filter shops based on revenue thresholds and contact information availability
- 🔄 **Resume Capability**: Automatically resumes scraping from where it left off using backup files
- 🛡️ **Rate Limiting Protection**: Built-in retry logic with exponential backoff to handle API rate limits
- 📝 **Comprehensive Logging**: Detailed logging system for monitoring scraping progress and debugging

## 📋 Prerequisites

- 🐍 Python 3.7+
- 🌐 Chrome browser installed
- 🔑 Valid EverBee account and login credentials
- 📁 `category_m.json` file containing Etsy category URLs

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/etsy-scraper.git
cd etsy-scraper
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## 📦 Required Dependencies

```
requests
undetected-chromedriver
selenium
beautifulsoup4
cloudscraper
```

## ⚙️ Setup

1. **🔐 EverBee Authentication**: 
   - The script will automatically open EverBee in Chrome
   - Login manually when prompted
   - The script will extract and store your authentication token

2. **📂 Category Data**:
   - Ensure `category_m.json` exists in the project directory
   - This file should contain structured category data with URLs to scrape

## 🎮 Usage

Run the script and choose your extraction mode:

```bash
python main.py
```

### 🎯 Extraction Modes

1. **📧 Extract if email**: Only saves shops that have email addresses
2. **📱 Extract if phone number**: Only saves shops that have phone numbers  
3. **📧📱 Extract if email AND phone number**: Only saves shops that have both
4. **📧📱 Extract if email OR phone number**: Saves shops that have either contact method

## 📄 Output Files

- **📊 `shop_data.csv`**: Main output file containing all scraped shop data
- **📋 `scraper.log`**: Detailed logging information
- **❌ `unprocessed_shops.txt`**: List of shops that couldn't be processed due to errors

### 📈 CSV Output Format

| Column | Description |
|--------|-------------|
| 🏪 Shop Name | Etsy shop name |
| 🔗 Shop URL | Direct link to the Etsy shop |
| 📊 Sales Number | Total number of sales |
| 💰 Average Product Price | Average price of products (from EverBee) |
| 💵 Monthly Revenue | Estimated monthly revenue (from EverBee) |
| 📱 Phone | Extracted phone numbers |
| 📧 Email | Extracted email addresses |

## 🔧 Configuration

### 💰 Revenue Filtering
The script automatically filters out shops with monthly revenue less than $5,000. You can modify this threshold in the `main()` function:

```python
if monthly_revenue < 5000:  # Change this value
    continue
```

### ⏱️ Rate Limiting
Default settings include:
- ⏰ Initial delay: 30 seconds for API requests
- 🎲 Random delays: 1-3 seconds between shop requests
- 📦 Batch processing: 5 shops before taking a break

## 📞 Contact Information Sources

The scraper attempts to extract contact information from:
- 📱 Shop's social media profiles (Instagram, Facebook, Pinterest, Twitter/X)
- 🌐 Shop's external website links
- 📄 About/Contact pages
- 📝 Social media bio sections

## 🛠️ Error Handling

- **⏳ Rate Limiting**: Automatic retry with exponential backoff
- **🌐 Network Errors**: Request retry logic with configurable attempts
- **❌ Invalid Data**: Graceful error handling with logging
- **🔄 Resume Capability**: Automatically skips already processed shops

## 📊 Logging

The script creates detailed logs including:
- 📈 Processing progress
- 🔄 API response status
- ❌ Error messages and stack traces
- ⏰ Rate limiting notifications
- 📊 Shop processing statistics

## ⚖️ Legal Considerations

⚠️ **Important**: This tool is for educational and research purposes only. Please ensure you comply with:
- 📋 Etsy's Terms of Service
- 🔒 Applicable data protection laws (GDPR, CCPA, etc.)
- 🌐 Website scraping best practices
- ⏱️ Rate limiting and respectful scraping practices

## 🔧 Troubleshooting

### ❓ Common Issues

1. **🌐 Chrome Driver Issues**:
   - Ensure Chrome browser is installed and up to date
   - The script uses undetected-chromedriver which should handle driver management

2. **🔑 EverBee Authentication**:
   - Make sure you're logged into EverBee in the browser
   - Token extraction happens automatically after login

3. **⏰ Rate Limiting**:
   - The script includes built-in rate limiting
   - If you encounter persistent rate limits, consider increasing delay times

4. **📁 Missing category_m.json**:
   - Ensure the category file exists and contains valid JSON structure
   - Check that URLs in the category file are accessible

## 🤝 Contributing

1. 🍴 Fork the repository
2. 🌟 Create a feature branch (`git checkout -b feature/amazing-feature`)
3. 💾 Commit your changes (`git commit -m 'Add some amazing feature'`)
4. 📤 Push to the branch (`git push origin feature/amazing-feature`)
5. 🔄 Open a Pull Request

## ⚠️ Disclaimer

This tool is provided as-is for educational purposes. Users are responsible for ensuring their use complies with all applicable laws and website terms of service. The authors are not responsible for any misuse of this tool.

## 🆘 Support

If you encounter issues or have questions:
1. 🔍 Check the existing issues on GitHub
2. 📋 Review the log files for error details
3. 🆕 Create a new issue with detailed information about the problem
