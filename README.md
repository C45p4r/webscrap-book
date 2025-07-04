# OVERLORD Book Processing System

A unified system for web scraping, translating, and formatting Chinese books for iPhone reading.

## 🚀 Features

- **Web Scraping**: Automatic extraction of book chapters from Bilibili
- **Translation**: Simplified Chinese to Traditional Chinese conversion
- **iPhone Optimization**: Text formatting optimized for mobile reading
- **Chapter Management**: Automatic chapter sequencing and indexing
- **Unified Workflow**: All processes integrated into a single system

## 📁 Project Structure

```text
automate-book-finder/
├── main.py                 # Main unified processing system
├── requirements.txt        # Python dependencies
├── prompt.md              # Project documentation
├── testing/               # Testing and debugging scripts
│   ├── README.md          # Testing documentation
│   ├── test-*.py          # Various test scripts
│   └── debug_*.py         # Debug utilities
├── OVERLORD/              # Original scraped chapters
├── OVERLORD_Traditional/  # Processed Traditional Chinese chapters
└── .venv/                 # Virtual environment (optional)
```

## 🔧 Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd automate-book-finder
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Chrome WebDriver**:
   - Chrome browser must be installed
   - ChromeDriver will be automatically managed by webdriver-manager

## 📖 Usage

### Quick Start

Run the main system:

```bash
python main.py
```

### Menu Options

1. **🔄 Run Full Workflow**: Complete automation (scrape + translate + format + index)
2. **🌐 Web Scraping Only**: Extract chapters from web
3. **🔤 Translation Only**: Convert existing chapters to Traditional Chinese
4. **📝 Update Titles Only**: Update chapter titles in Traditional Chinese
5. **🗂️ Fix Chapter Sequence Only**: Reorder chapters according to original sequence
6. **❌ Exit**: Close the application

### Full Workflow Process

1. **Web Scraping**:

   - Opens Chrome browser
   - Handles CAPTCHA (manual resolution)
   - Extracts chapter content automatically

2. **Translation**:

   - Converts Simplified Chinese to Traditional Chinese
   - Uses OpenCC for accurate conversion
   - Parallel processing for efficiency

3. **iPhone Optimization**:

   - 35-character line length for optimal mobile reading
   - Proper paragraph spacing
   - Mobile-friendly formatting

4. **Chapter Management**:
   - Automatic chapter sequencing
   - Title updates and formatting
   - README generation with processing details

## 🛠️ Technical Details

### Dependencies

- **selenium**: Web scraping automation
- **beautifulsoup4**: HTML parsing
- **opencc-python-reimplemented**: Chinese text conversion
- **webdriver-manager**: Automatic WebDriver management

### Supported Formats

- **Input**: Bilibili Opus pages
- **Output**: Traditional Chinese text files
- **Optimization**: iPhone screen reading

### Processing Features

- **Parallel Processing**: Multi-threaded translation
- **Error Handling**: Comprehensive error recovery
- **Progress Tracking**: Real-time processing updates
- **Resource Management**: Automatic cleanup

## 📱 Mobile Optimization

The system specifically optimizes text for iPhone reading:

- **Line Length**: 35 characters per line
- **Paragraph Spacing**: Enhanced readability
- **Font Compatibility**: Traditional Chinese character support
- **Night Mode**: Compatible with dark mode reading

## 🔍 Testing

Testing scripts are available in the `testing/` directory:

- Web scraping tests
- Translation accuracy tests
- Format validation tests
- Chrome WebDriver tests

## 📝 Configuration

The system uses default configuration suitable for OVERLORD processing:

- **Source URL**: Bilibili Opus pages
- **Output Directory**: `OVERLORD/` and `OVERLORD_Traditional/`
- **Translation Config**: Simplified to Traditional Chinese
- **Format**: iPhone optimized

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes using the testing scripts
4. Submit a pull request

## 📄 License

This project is for educational and personal use. Please respect the original content creators and website terms of service.

## 🙏 Acknowledgments

- OpenCC for Chinese text conversion
- Selenium for web automation
- The original content creators

---

**Note**: This system is designed for personal use and educational purposes. Always respect website terms of service and copyright laws when scraping content.
