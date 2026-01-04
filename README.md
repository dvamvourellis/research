# AI Trends Investment Portfolio Generator

An automated system that analyzes recent AI trends from trusted sources and generates data-driven investment portfolios for a 1-2 year horizon.

## Overview

This system performs the following steps:

1. **Fetches AI Trends** - Collects content from trusted sources:
   - [Epoch AI](https://epoch.ai/)
   - [Dwarkesh Patel's AI Buildout Analysis](https://www.dwarkesh.com/p/thoughts-on-the-ai-buildout)
   - [Dwarkesh Patel's AI Progress Analysis](https://www.dwarkesh.com/p/thoughts-on-ai-progress-dec-2025)
   - [AI-2027 Forecasting](https://ai-2027.com/)

2. **Analyzes Trends** - Uses Claude AI to extract:
   - Key trends with supporting evidence
   - Specific data points (e.g., compute gaps, supply chain bottlenecks)
   - Supply chain insights
   - Technology trends

3. **Generates Investment Themes** - Converts trends into actionable investment themes across the AI value chain

4. **Identifies Stock Tickers** - Finds publicly traded companies matching the themes

5. **Validates Tickers** - Validates against:
   - Recent news and market sentiment
   - Fundamental metrics (P/E, growth, margins)
   - Theme alignment

6. **Allocates Portfolio** - Calculates optimal portfolio weights with:
   - Risk-adjusted allocations
   - Diversification across themes
   - Core/Satellite/Tactical structure

## Installation

### Prerequisites

- Python 3.8 or higher
- Anthropic API key (get one at [anthropic.com](https://console.anthropic.com/))

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd research
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API key:
```bash
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

## Usage

### Basic Usage

Run the complete pipeline with default settings (100k capital, max 15 positions):

```bash
python main.py
```

### Custom Parameters

Specify custom capital amount and position limits:

```bash
python main.py --capital 250000 --max-positions 20
```

### Skip Fetching (Use Existing Data)

If you've already fetched data and want to re-run analysis:

```bash
python main.py --skip-fetch
```

### Run Individual Modules

You can also run each module independently:

```bash
# Fetch AI trends
python -m src.data_fetcher.fetcher

# Analyze trends
python -m src.trend_analyzer.analyzer

# Generate investment themes
python -m src.investment_themes.theme_generator

# Find tickers
python -m src.ticker_finder.finder

# Validate tickers
python -m src.validator.validator

# Calculate allocations
python -m src.portfolio_allocator.allocator
```

## Output Files

The system generates the following outputs:

### Data Files (JSON)
- `data/fetched_content.json` - Raw content from AI sources
- `data/trend_analysis.json` - Extracted trends and data points
- `data/investment_themes.json` - Generated investment themes
- `data/ticker_recommendations.json` - Identified stock tickers
- `data/ticker_validation.json` - Validation results with scores
- `data/portfolio_allocation.json` - Portfolio allocation details

### Reports
- `data/portfolio_allocation.csv` - Portfolio in spreadsheet format
- `reports/investment_report.md` - Comprehensive markdown report

## Project Structure

```
research/
├── src/
│   ├── data_fetcher/         # Fetches content from AI sources
│   ├── trend_analyzer/       # Analyzes trends using Claude
│   ├── investment_themes/    # Generates investment themes
│   ├── ticker_finder/        # Finds matching stock tickers
│   ├── validator/            # Validates tickers and fundamentals
│   └── portfolio_allocator/  # Calculates portfolio weights
├── data/                     # Output data files
├── reports/                  # Generated reports
├── main.py                   # Main orchestration script
└── requirements.txt          # Python dependencies
```

## Data Sources

### AI Trends (Web Scraping)
- **Epoch AI Blog**: Research articles on AI compute trends, training costs, and scaling
- **Dwarkesh Patel's Blog**: In-depth analysis of AI infrastructure buildout and progress
- **AI-2027 Forecasting**: Forward-looking AI development scenarios

**Note**: For Epoch AI, the system fetches their blog/research section. Since these sites publish new content regularly, you can customize the URLs in `src/data_fetcher/fetcher.py` to point to specific articles or add additional sources.

### Market Data (Yahoo Finance via yfinance)
All stock fundamentals, prices, news, and analyst data come from **Yahoo Finance**:
- **Free and reliable** for basic fundamental analysis
- **15-20 minute delays** on some real-time data
- **Limited news coverage** compared to premium services (Bloomberg, FactSet)
- **Aggregated analyst recommendations** from multiple sources

### AI Analysis (Anthropic Claude)
Claude AI (Sonnet 4.5) is used for:
- Extracting trends and insights from fetched content
- Generating investment themes from trend analysis
- Identifying relevant stock tickers for each theme
- Scoring and validating ticker recommendations
- Optimizing portfolio allocations

## How It Works

### 1. Data Collection

The system fetches content from specified AI trend sources using web scraping. Content is parsed and converted to markdown format for better structure preservation.

### 2. Trend Analysis

Claude AI analyzes the fetched content to identify:
- **Key Trends**: Major developments in AI infrastructure and deployment
- **Data Points**: Specific metrics like compute requirements, supply constraints
- **Supply Chain Insights**: Bottlenecks and opportunities (e.g., CoWoS capacity at TSMC)
- **Technology Trends**: Emerging technologies and adoption patterns

### 3. Investment Theme Generation

Based on the trend analysis, the system generates investment themes covering:
- **Semiconductors**: Chip design, manufacturing, packaging
- **Hardware/Infrastructure**: Servers, networking, data centers
- **Cloud Compute**: Cloud providers, compute-as-a-service
- **Software**: AI models, platforms, applications
- **Data Infrastructure**: Storage, processing, pipelines
- **Energy/Power**: Data center power, cooling

Each theme includes:
- Rationale based on identified trends
- Key drivers and supporting data
- Risk factors
- Value chain position (upstream/midstream/downstream)
- Confidence level

### 4. Ticker Identification

Claude AI identifies publicly traded stocks matching each theme, considering:
- Direct exposure to the theme
- Market position and competitive advantages
- Financial health and growth
- Liquidity and trading volume

Tickers are validated using yfinance to ensure they're real and tradeable.

### 5. Validation

Each ticker is validated using data from **Yahoo Finance** (via yfinance library):
- **Fundamentals**: P/E ratio, revenue/earnings growth, profit margins, debt-to-equity
- **Market Data**: Price momentum, 52-week ranges, trading volume
- **Analyst Recommendations**: Aggregated analyst ratings and price targets
- **Recent News**: Headlines aggregated by Yahoo Finance (limited coverage)
- **Theme Alignment**: Claude AI analysis of fit with investment themes

**Note**: Yahoo Finance data is free but may have 15-20 minute delays and limited news coverage compared to premium services like Bloomberg or FactSet.

Claude AI scores each ticker on:
- Theme alignment (1-10)
- Fundamental quality (1-10)
- Market sentiment (1-10)
- Overall score and recommendation (Buy/Hold/Pass)

### 6. Portfolio Allocation

The system calculates optimal portfolio weights using a tiered approach:

- **Core Holdings** (40-60%): Highest conviction, lowest risk
- **Satellite Holdings** (30-40%): Strong conviction, moderate risk
- **Tactical Holdings** (10-20%): Opportunistic, higher risk/reward

Risk management includes:
- Maximum single position limits
- Sector exposure limits
- Cash buffer
- Rebalancing guidance

## Example Output

The system generates output like:

```
PORTFOLIO ALLOCATION
================================================================================

💰 Total Capital: $100,000.00
📊 Total Allocated: $95,000.00
💵 Cash Remaining: $5,000.00
🎯 Number of Positions: 12

CORE (55.0%):
  NVDA
    Weight: 15.0% | Amount: $15,000.00
    Score: 9.2/10 (Theme: 10/10, Fundamentals: 9/10)
    Rationale: Leading AI chip designer with dominant position in datacenter GPUs...

  TSM
    Weight: 12.0% | Amount: $12,000.00
    Score: 8.8/10 (Theme: 9/10, Fundamentals: 9/10)
    Rationale: Critical foundry partner with advanced packaging capabilities...
```

## Limitations & Disclaimers

### Limitations

- **Data Freshness**: Web scraping may not capture the most recent updates
- **Analysis Quality**: Depends on the quality of source content
- **Market Data**: Uses publicly available data which may have delays
- **No Backtesting**: This is a forward-looking research tool, not a backtested strategy

### Disclaimer

**This system is for research and educational purposes only. It does not constitute financial advice.**

- Always conduct your own research
- Consult with a qualified financial advisor before making investment decisions
- Past performance does not guarantee future results
- All investments carry risk, including loss of principal
- The system uses AI analysis which may contain errors or biases

## Customization

### Adding New Sources

Edit `src/data_fetcher/fetcher.py` and add URLs to the `sources` dictionary:

```python
self.sources = {
    'epoch_ai': 'https://epoch.ai/',
    'your_source': 'https://your-source.com/article',
    # ...
}
```

### Adjusting Analysis Prompts

Each module has customizable prompts for Claude AI. Edit the relevant `*_prompt` strings in:
- `src/trend_analyzer/analyzer.py`
- `src/investment_themes/theme_generator.py`
- `src/ticker_finder/finder.py`
- `src/validator/validator.py`
- `src/portfolio_allocator/allocator.py`

### Changing Risk Parameters

Modify the allocation logic in `src/portfolio_allocator/allocator.py` to adjust:
- Position size limits
- Sector concentration limits
- Core/Satellite/Tactical ratios
- Cash buffer requirements

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add your license here]

## Acknowledgments

- AI trend sources: Epoch AI, Dwarkesh Patel, AI-2027
- Powered by Claude AI from Anthropic
- Market data from Yahoo Finance (yfinance)

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation
- Review the code comments

---

**Remember**: This is a research tool. Always do your own due diligence before investing.