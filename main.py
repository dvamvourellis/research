#!/usr/bin/env python3
"""
AI Trends Investment Portfolio Generator

This script orchestrates the entire pipeline:
1. Fetch AI trends from trusted sources
2. Analyze trends and extract data points
3. Generate investment themes
4. Identify matching stock tickers
5. Validate tickers against fundamentals and news
6. Calculate optimal portfolio allocation

Usage:
    python main.py [--capital AMOUNT] [--max-positions N]
"""

import argparse
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from src.data_fetcher.fetcher import AITrendsFetcher
from src.trend_analyzer.analyzer import TrendAnalyzer
from src.investment_themes.theme_generator import InvestmentThemeGenerator
from src.ticker_finder.finder import TickerFinder
from src.validator.validator import TickerValidator
from src.portfolio_allocator.allocator import PortfolioAllocator


def setup_environment():
    """Load environment variables and check requirements."""
    load_dotenv()

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("Please set it in a .env file or export it in your shell.")
        sys.exit(1)

    # Create data directory
    os.makedirs('data', exist_ok=True)
    os.makedirs('reports', exist_ok=True)


def run_pipeline(capital: float = 100000.0, max_positions: int = 15, skip_fetch: bool = False):
    """
    Run the complete investment research pipeline.

    Args:
        capital: Total capital to allocate
        max_positions: Maximum number of positions in portfolio
        skip_fetch: Skip fetching (use existing data)
    """
    print("\n" + "="*80)
    print("AI TRENDS INVESTMENT PORTFOLIO GENERATOR")
    print("="*80)
    print(f"Target Capital: ${capital:,.2f}")
    print(f"Max Positions: {max_positions}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # Step 1: Fetch AI trends
        if not skip_fetch:
            print("\n" + "🔍 STEP 1: Fetching AI Trends from Sources")
            print("-"*80)
            fetcher = AITrendsFetcher()
            content = fetcher.fetch_all_sources()
            fetcher.save_to_file(content)
            print("✓ Trend data fetched and saved")
        else:
            print("\n🔍 STEP 1: Skipping fetch (using existing data)")
            import json
            with open('data/fetched_content.json', 'r') as f:
                content = json.load(f)

        # Step 2: Analyze trends
        print("\n" + "📊 STEP 2: Analyzing Trends and Extracting Data Points")
        print("-"*80)
        analyzer = TrendAnalyzer()
        analysis = analyzer.analyze_content(content)
        analyzer.save_analysis(analysis)
        analyzer.print_summary(analysis)
        print("✓ Trend analysis complete")

        # Step 3: Generate investment themes
        print("\n" + "💡 STEP 3: Generating Investment Themes")
        print("-"*80)
        theme_generator = InvestmentThemeGenerator()
        themes = theme_generator.generate_themes(analysis)
        theme_generator.save_themes(themes)
        theme_generator.print_summary(themes)
        print("✓ Investment themes generated")

        # Step 4: Find matching tickers
        print("\n" + "🔎 STEP 4: Identifying Stock Tickers")
        print("-"*80)
        ticker_finder = TickerFinder()
        tickers = ticker_finder.find_tickers(themes)
        ticker_finder.save_tickers(tickers)
        ticker_finder.print_summary(tickers)
        print("✓ Tickers identified and validated")

        # Step 5: Validate tickers
        print("\n" + "✅ STEP 5: Validating Tickers")
        print("-"*80)
        validator = TickerValidator()
        validation = validator.validate_tickers(tickers, themes)
        validator.save_validation(validation)
        validator.print_summary(validation)
        print("✓ Ticker validation complete")

        # Step 6: Calculate portfolio allocation
        print("\n" + "💼 STEP 6: Calculating Portfolio Allocation")
        print("-"*80)
        allocator = PortfolioAllocator()
        portfolio = allocator.allocate_portfolio(validation, themes, capital, max_positions)
        allocator.save_portfolio(portfolio)
        allocator.export_to_csv(portfolio)
        allocator.print_summary(portfolio)
        print("✓ Portfolio allocation complete")

        # Generate final report
        print("\n" + "📄 STEP 7: Generating Final Report")
        print("-"*80)
        generate_report(analysis, themes, validation, portfolio)
        print("✓ Report generated")

        print("\n" + "="*80)
        print("✅ PIPELINE COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\nOutput files:")
        print("  - data/fetched_content.json")
        print("  - data/trend_analysis.json")
        print("  - data/investment_themes.json")
        print("  - data/ticker_recommendations.json")
        print("  - data/ticker_validation.json")
        print("  - data/portfolio_allocation.json")
        print("  - data/portfolio_allocation.csv")
        print("  - reports/investment_report.md")
        print("\n")

    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def generate_report(analysis, themes, validation, portfolio):
    """Generate a comprehensive markdown report."""

    report = []
    report.append("# AI Trends Investment Portfolio Report")
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\n---\n")

    # Executive Summary
    report.append("## Executive Summary\n")
    summary = portfolio.get('summary', {})
    report.append(f"- **Total Capital**: ${summary.get('total_capital', 0):,.2f}")
    report.append(f"- **Number of Positions**: {summary.get('number_of_positions', 0)}")
    report.append(f"- **Cash Buffer**: ${summary.get('cash_remaining', 0):,.2f}")

    portfolio_summary = validation.get('analysis', {}).get('portfolio_summary', {})
    if portfolio_summary.get('risk_assessment'):
        report.append(f"\n**Risk Assessment**: {portfolio_summary['risk_assessment']}")

    # Key Trends
    report.append("\n---\n")
    report.append("## Key AI Trends Identified\n")
    for i, trend in enumerate(analysis.get('key_trends', [])[:10], 1):
        report.append(f"\n### {i}. {trend.get('trend', 'N/A')}")
        report.append(f"\n**Importance**: {trend.get('importance', 'N/A')} | "
                     f"**Time Horizon**: {trend.get('time_horizon', 'N/A')}")
        report.append(f"\n{trend.get('evidence', 'N/A')}\n")

    # Investment Themes
    report.append("\n---\n")
    report.append("## Investment Themes\n")
    for i, theme in enumerate(themes.get('investment_themes', []), 1):
        report.append(f"\n### {i}. {theme.get('theme_name', 'N/A')}")
        report.append(f"\n**Confidence**: {theme.get('confidence_level', 'N/A')} | "
                     f"**Value Chain**: {theme.get('value_chain_position', 'N/A')}")
        report.append(f"\n{theme.get('description', 'N/A')}")
        report.append(f"\n**Rationale**: {theme.get('rationale', 'N/A')}\n")

    # Portfolio Allocation
    report.append("\n---\n")
    report.append("## Portfolio Allocation\n")

    allocations = portfolio.get('allocations', [])
    if allocations:
        report.append("\n| Ticker | Weight | Amount | Tier | Score | Rationale |")
        report.append("|--------|--------|--------|------|-------|-----------|")

        for alloc in sorted(allocations, key=lambda x: x['weight_percent'], reverse=True):
            report.append(
                f"| {alloc['symbol']} | "
                f"{alloc['weight_percent']:.1f}% | "
                f"${alloc['dollar_allocation']:,.0f} | "
                f"{alloc['tier']} | "
                f"{alloc['overall_score']:.1f}/10 | "
                f"{alloc['rationale'][:50]}... |"
            )

    # Strategy
    strategy = portfolio.get('allocation_strategy', '')
    if strategy:
        report.append(f"\n### Allocation Strategy\n\n{strategy}\n")

    # Risk Management
    risk_mgmt = portfolio.get('risk_management', {})
    if risk_mgmt:
        report.append("\n### Risk Management Guidelines\n")
        report.append(f"- **Max Single Position**: {risk_mgmt.get('max_single_position', 'N/A')}%")
        report.append(f"- **Max Sector Exposure**: {risk_mgmt.get('max_sector_exposure', 'N/A')}%")
        report.append(f"- **Cash Buffer**: {risk_mgmt.get('cash_buffer', 'N/A')}%")
        if risk_mgmt.get('notes'):
            report.append(f"\n{risk_mgmt['notes']}\n")

    # Rebalancing Guidance
    rebalancing = portfolio.get('rebalancing_guidance', {})
    if rebalancing:
        report.append("\n### Rebalancing Guidance\n")
        report.append(f"- **Frequency**: {rebalancing.get('frequency', 'N/A')}")
        if rebalancing.get('triggers'):
            report.append(f"- **Triggers**: {', '.join(rebalancing['triggers'])}")
        if rebalancing.get('exit_criteria'):
            report.append(f"- **Exit Criteria**: {', '.join(rebalancing['exit_criteria'])}")

    # Detailed Ticker Analysis
    report.append("\n---\n")
    report.append("## Detailed Ticker Analysis\n")

    ticker_analysis = validation.get('analysis', {}).get('ticker_analysis', [])
    for ta in sorted(ticker_analysis, key=lambda x: x.get('overall_score', 0), reverse=True):
        if ta.get('recommendation') == 'Buy':
            report.append(f"\n### {ta['symbol']} - {ta['recommendation']}")
            report.append(f"\n**Overall Score**: {ta.get('overall_score', 0)}/10")
            report.append(f"\n**Scores**: Theme Alignment: {ta.get('theme_alignment_score', 0)}/10 | "
                         f"Fundamentals: {ta.get('fundamental_quality_score', 0)}/10 | "
                         f"Sentiment: {ta.get('market_sentiment_score', 0)}/10")
            report.append(f"\n**Rationale**: {ta.get('rationale', 'N/A')}")

            if ta.get('key_strengths'):
                report.append(f"\n**Strengths**:")
                for strength in ta['key_strengths']:
                    report.append(f"- {strength}")

            if ta.get('key_risks'):
                report.append(f"\n**Risks**:")
                for risk in ta['key_risks']:
                    report.append(f"- {risk}")

            report.append("\n")

    # Disclaimer
    report.append("\n---\n")
    report.append("## Disclaimer\n")
    report.append("\nThis report is generated by an AI system for research purposes only. "
                 "It does not constitute financial advice. Always conduct your own research "
                 "and consult with a qualified financial advisor before making investment decisions. "
                 "Past performance does not guarantee future results.\n")

    # Write report
    report_text = '\n'.join(report)
    with open('reports/investment_report.md', 'w', encoding='utf-8') as f:
        f.write(report_text)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate AI trends-based investment portfolio'
    )
    parser.add_argument(
        '--capital',
        type=float,
        default=100000.0,
        help='Total capital to allocate (default: 100000)'
    )
    parser.add_argument(
        '--max-positions',
        type=int,
        default=15,
        help='Maximum number of positions (default: 15)'
    )
    parser.add_argument(
        '--skip-fetch',
        action='store_true',
        help='Skip fetching new data (use existing)'
    )

    args = parser.parse_args()

    # Setup
    setup_environment()

    # Run pipeline
    run_pipeline(
        capital=args.capital,
        max_positions=args.max_positions,
        skip_fetch=args.skip_fetch
    )


if __name__ == "__main__":
    main()
