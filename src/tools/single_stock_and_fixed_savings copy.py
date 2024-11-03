from langchain_core.tools import tool
import yfinance as yf
import pandas as pd

def fetch_stock_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch historical stock data for a given symbol and date range using yfinance.

    Args:
        symbol (str): Stock ticker symbol (e.g., 'AAPL')
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
    """
    data = yf.download(symbol, start=start_date, end=end_date)
    # Convert timezone-aware timestamps to timezone-naive timestamps
    data.index = data.index.tz_localize(None)
    return data



def backtest_mixed_investment(data, start_date, end_date, monthly_investment, stock_allocation, savings_rate, symbol):
    investment_dates = []
    stock_shares = 0
    savings_balance = 0
    total_invested = 0
    stock_value = []
    savings_value = []

    stock_investment = monthly_investment * stock_allocation
    savings_investment = monthly_investment * (1 - stock_allocation)
    daily_rate = (1 + savings_rate) ** (1/365) - 1

    current_date = pd.to_datetime(start_date).normalize()
    prev_date = current_date
    end_date = pd.to_datetime(end_date).normalize()
    
    adj_close = data[('Adj Close', symbol)]
    while current_date <= pd.to_datetime(end_date):
        if current_date in adj_close.index:
            price = adj_close[current_date]
            new_shares = stock_investment / price
            stock_shares += new_shares

            days_passed = (current_date - prev_date).days
            savings_balance *= (1 + daily_rate) ** days_passed
            savings_balance += savings_investment

            total_invested += monthly_investment

            investment_dates.append(current_date)
            stock_value.append(stock_shares * price)
            savings_value.append(savings_balance)

            prev_date = current_date

        current_date += pd.DateOffset(months=1)

    stock_value_series = pd.Series(stock_value, index=investment_dates).reindex(adj_close.index, method='ffill')
    savings_value_series = pd.Series(savings_value, index=investment_dates).reindex(adj_close.index, method='ffill')
    portfolio_value = stock_value_series + savings_value_series

    return portfolio_value, stock_value_series, savings_value_series, total_invested

# @tool
def analyze_single_stock_and_fixed_savings(
    symbol: str,
    start_date: str,
    end_date: str,
    monthly_investment: float,
    stock_allocation: float = 1.0,
    savings_rate: float = 0.045
) -> str:
    """
    Backtest an investment strategy mixing a stock ticker and high-yield savings/fd fixed deposit account.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        monthly_investment: Monthly investment amount
        stock_allocation: Percentage allocated to stocks (0.0 to 1.0)
        savings_rate: Annual interest rate for savings (as decimal)
    
    Returns:
        String with detailed investment analysis
    """
    try:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        data = fetch_stock_data(symbol, start, end)
        
        if data.empty:
            return f"No data available for {symbol} in the specified date range."
        
        portfolio_value, stock_value, savings_value, total_invested = backtest_mixed_investment(
            data, start_date, end_date, monthly_investment, stock_allocation, savings_rate, symbol
        )

        print(total_invested)
        
        # Calculate total years and returns
        total_years = (end - start).days / 365.25
        total_return = ((portfolio_value[-1] - total_invested) / total_invested * 100)
        annualized_return = ((portfolio_value[-1] / total_invested) ** (1/total_years) - 1) * 100
        
        # Create detailed report
        report = [
            f"\nInvestment Backtest Results for {symbol}",
            f"Period: {start_date} to {end_date} ({total_years:.1f} years)",
            f"\nStrategy:",
            f"- Monthly Investment: ${monthly_investment:,.2f}",
            f"- Stock Allocation: {stock_allocation*100:.1f}%",
            f"- Savings Rate: {savings_rate*100:.1f}%",
            f"\nResults:",
            f"Total Invested: ${total_invested:,.2f}",
            f"Final Portfolio Value: ${portfolio_value[-1]:,.2f}",
            f"- Stock Value: ${stock_value[-1]:,.2f}",
            f"- Savings Value: ${savings_value[-1]:,.2f}",
            f"Total Return: {total_return:.2f}%",
            f"Annualized Return: {annualized_return:.2f}%"
        ]
        
        return "\n".join(report)
        
    except Exception as e:
        return f"Error during backtesting: {str(e)}"

if __name__ == "__main__":
    result = analyze_single_stock_and_fixed_savings.run({
        "symbol": 'AAPL',
        "start_date": '2015-01-01',
        "end_date": '2024-01-01',
        "monthly_investment": 150,
        "stock_allocation": 0.66,
        "savings_rate": 0.07
    })
    print(result)