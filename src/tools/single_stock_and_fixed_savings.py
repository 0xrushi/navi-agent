import pandas as pd
import yfinance as yf
from typing import List, Dict, Tuple, Union
import pandas as pd
import yfinance as yf
from typing import List, Dict, Tuple, Union
import pandas as pd
import yfinance as yf
from typing import List, Dict, Tuple, Union
from langchain_core.tools import tool

def fetch_stock_data(symbols: List[str], start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch historical stock data for multiple symbols and date range using yfinance.
    
    Args:
        symbols (List[str]): List of stock ticker symbols (e.g., ['AAPL', 'GOOGL'])
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
    """
    dfs = {}
    for symbol in symbols:
        symbol_data = yf.download(symbol, start=start_date, end=end_date)
        symbol_data.index = symbol_data.index.tz_localize(None)
        dfs[symbol] = symbol_data[('Adj Close', symbol)]
    
    # Combine all stock data into a single DataFrame
    if len(dfs) == 1:
        # Handle single stock case
        symbol = symbols[0]
        return pd.DataFrame({symbol: dfs[symbol]})
    else:
        return pd.DataFrame(dfs)

def backtest_mixed_portfolio(
    data: pd.DataFrame,
    start_date: str,
    end_date: str,
    monthly_investment: float,
    allocations: Dict[str, float],
    savings_rates: Dict[str, float]
) -> Tuple[pd.Series, Dict[str, pd.Series], Dict[str, pd.Series], float]:
    """
    Backtest a portfolio with multiple stocks and fixed-rate investments.
    """
    investment_dates = []
    stock_shares = {symbol: 0 for symbol in allocations if symbol in data.columns}
    savings_balances = {name: 0 for name in savings_rates}
    total_invested = 0
    
    # Initialize value tracking dictionaries
    stock_values = {symbol: [] for symbol in stock_shares}
    savings_values = {name: [] for name in savings_rates}
    
    # Calculate investment amounts for each asset
    investment_amounts = {
        asset: monthly_investment * alloc 
        for asset, alloc in allocations.items()
    }

    # Convert savings rates to daily
    daily_rates = {
        name: (1 + rate) ** (1/365) - 1 
        for name, rate in savings_rates.items()
    }

    current_date = pd.to_datetime(start_date).normalize()
    prev_date = current_date
    end_date = pd.to_datetime(end_date).normalize()
    
    while current_date <= end_date:
        # Check if we have stock data for this date
        if current_date in data.index:
            prices = data.loc[current_date]
            
            # Process stock investments
            for symbol in stock_shares:
                if not pd.isna(prices[symbol]):
                    price = prices[symbol]
                    new_shares = investment_amounts.get(symbol, 0) / price
                    stock_shares[symbol] += new_shares
                    stock_values[symbol].append(stock_shares[symbol] * price)

            # Process savings accounts
            days_passed = (current_date - prev_date).days
            for name in savings_balances:
                savings_balances[name] *= (1 + daily_rates[name]) ** days_passed
                savings_balances[name] += investment_amounts.get(name, 0)
                savings_values[name].append(savings_balances[name])

            total_invested += monthly_investment
            investment_dates.append(current_date)
            prev_date = current_date

        current_date += pd.DateOffset(months=1)

    if not investment_dates:
        raise ValueError("No valid investment dates found in the given date range")

    # Convert to time series
    stock_value_series = {}
    for symbol in stock_shares:
        if stock_values[symbol]:  # Check if we have any values
            series = pd.Series(stock_values[symbol], index=investment_dates)
            stock_value_series[symbol] = series.reindex(data.index, method='ffill')

    savings_value_series = {}
    for name in savings_balances:
        if savings_values[name]:  # Check if we have any values
            series = pd.Series(savings_values[name], index=investment_dates)
            savings_value_series[name] = series.reindex(data.index, method='ffill')

    # Calculate total portfolio value
    portfolio_value = pd.Series(0, index=data.index)
    for series in stock_value_series.values():
        portfolio_value += series.fillna(0)
    for series in savings_value_series.values():
        portfolio_value += series.fillna(0)

    return portfolio_value, stock_value_series, savings_value_series, total_invested

@tool
def analyze_single_stock_and_fixed_savings(
    symbols: List[str],
    start_date: str,
    end_date: str,
    monthly_investment: float,
    allocations: Dict[str, float],
    savings_rates: Dict[str, float]
) -> str:
    """
    Backtest an investment strategy mixing multiple stocks and fixed-rate investments.
    
    Args:
        symbols: List of stock symbols (e.g., ['AAPL', 'GOOGL'])
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        monthly_investment: Total monthly investment amount
        allocations: Dictionary mapping assets to their allocation percentages
        savings_rates: Dictionary mapping savings accounts to their annual interest rates
    
    Returns:
        String with detailed investment analysis
    """
    try:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # Validate allocations sum to 1
        if not abs(sum(allocations.values()) - 1.0) < 0.0001:
            return "Error: Asset allocations must sum to 100%"
        
        # Validate symbols match allocations
        stock_symbols = [symbol for symbol in allocations if symbol not in savings_rates]
        if set(symbols) != set(stock_symbols):
            return "Error: Mismatch between provided symbols and stock allocations"
        
        data = fetch_stock_data(symbols, start, end)
        
        if data.empty:
            return f"No data available for {symbols} in the specified date range."
        
        portfolio_value, stock_values, savings_values, total_invested = backtest_mixed_portfolio(
            data, start_date, end_date, monthly_investment, allocations, savings_rates
        )
        
        # Calculate returns
        total_years = (end - start).days / 365.25
        total_return = ((portfolio_value[-1] - total_invested) / total_invested * 100)
        annualized_return = ((portfolio_value[-1] / total_invested) ** (1/total_years) - 1) * 100
        
        # Create detailed report
        report = [
            f"\nPortfolio Backtest Results",
            f"Period: {start_date} to {end_date} ({total_years:.1f} years)",
            f"\nStrategy:",
            f"Monthly Investment: ${monthly_investment:,.2f}",
            "\nAllocations:"
        ]
        
        # Add allocation details
        for asset, alloc in allocations.items():
            report.append(f"- {asset}: {alloc*100:.1f}%")
        
        # Add savings rate details
        if savings_rates:
            report.append("\nSavings Rates:")
            for account, rate in savings_rates.items():
                report.append(f"- {account}: {rate*100:.1f}%")
        
        report.extend([
            f"\nResults:",
            f"Total Invested: ${total_invested:,.2f}",
            f"Final Portfolio Value: ${portfolio_value[-1]:,.2f}"
        ])
        
        # Add individual stock values
        for symbol, values in stock_values.items():
            report.append(f"- {symbol} Value: ${values[-1]:,.2f}")
            
        # Add individual savings values
        for account, values in savings_values.items():
            report.append(f"- {account} Value: ${values[-1]:,.2f}")
            
        report.extend([
            f"\nReturns:",
            f"Total Return: {total_return:.2f}%",
            f"Annualized Return: {annualized_return:.2f}%"
        ])
        
        return "\n".join(report)
        
    except Exception as e:
        return f"Error during backtesting: {str(e)}"
    
if __name__ == "__main__":
    symbols = ['AAPL', 'GOOGL']
    allocations = {
        'AAPL': 0.4,
        'GOOGL': 0.3,
        'High Yield Savings': 0.2,
        'Fixed Deposit': 0.1
    }
    savings_rates = {
        'High Yield Savings': 0.045,
        'Fixed Deposit': 0.06
    }

    result = analyze_single_stock_and_fixed_savings.run({
        "symbols": symbols,
        "start_date": '2020-01-01',
        "end_date": '2023-12-31',
        "monthly_investment": 1000,
        "allocations": allocations,
        "savings_rates": savings_rates
    })

    print(result)
