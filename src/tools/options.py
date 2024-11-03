from langchain_core.tools import tool
import mibian
import numpy as np
from datetime import datetime, timedelta

@tool
def calculate_option_profit(
    current_price: float,
    strike_price: float,
    days_to_expiry: int,
    option_type: str,
    initial_price: float,
    contracts: int = 1,
    interest_rate: float = 0.05
) -> str:
    """Calculate option profit/loss matrix for different price points and dates."""
    # Validate inputs
    if option_type not in ['p', 'c']:
        return "Error: option_type must be 'p' for put or 'c' for call"
    
    if current_price <= 0 or strike_price <= 0 or days_to_expiry < 0 or initial_price < 0:
        return "Error: prices and days must be positive numbers"
    
    if contracts < 1:
        return "Error: number of contracts must be at least 1"
    
    # Calculate implied volatility
    c = mibian.BS([current_price, strike_price, interest_rate, days_to_expiry], 
                  putPrice=initial_price if option_type == 'p' else None,
                  callPrice=initial_price if option_type == 'c' else None)
    implied_volatility = c.impliedVolatility

    total_cost = initial_price * 100 * contracts

    # Generate price range (±15% from current price)
    price_range = 0.15
    min_price = current_price * (1 - price_range)
    max_price = current_price * (1 + price_range)
    stock_prices = np.arange(min_price, max_price, current_price * 0.01)
    dates = [datetime.now() + timedelta(days=i) for i in range(days_to_expiry + 1)]

    data = np.zeros((len(stock_prices), len(dates)))

    for i, price in enumerate(stock_prices):
        for j, date in enumerate(dates):
            days_left = (dates[-1] - date).days

            if days_left == 0:
                option_value = max(strike_price - price, 0) if option_type == 'p' else max(price - strike_price, 0)
            else:
                c = mibian.BS([price, strike_price, interest_rate, days_left], volatility=implied_volatility)
                option_value = c.putPrice if option_type == 'p' else c.callPrice

            profit_loss = (option_value * 100 * contracts) - total_cost
            data[i, j] = round(profit_loss)

    # Format results
    result = f"Option Analysis:\n"
    result += f"Initial price: ${initial_price:.2f}\n"
    result += f"Total cost: ${total_cost:.2f}\n"
    result += f"Break-even at expiry: ${strike_price - initial_price if option_type == 'p' else strike_price + initial_price:.2f}\n"
    result += f"Implied Volatility: {implied_volatility:.2f}%\n\n"
    result += "Profit/Loss Matrix (rows=prices, columns=days):\n"
    result += str(np.flipud(data))
    
    return result 