from langchain_core.tools import tool
from typing import Optional

@tool
def calculate_compound_interest(
    start_age: int,
    monthly_investment: float,
    annual_return: float,
    future_age: int,
    stop_investing_age: Optional[int] = None,
    initial_investment: Optional[float] = 0
) -> str:
    """
    Calculate compound interest for investment over time with optional stop age and initial investment.
    Continues calculating returns until future_age even after stopping monthly investments.
    
    Args:
        start_age: Age when starting to invest
        monthly_investment: Monthly investment amount
        annual_return: Expected average annual return (as percentage, e.g., 8 for 8%)
        future_age: Age at which to calculate total returns
        stop_investing_age: Optional age to stop monthly investments (defaults to future_age)
        initial_investment: Optional initial lump sum investment (defaults to 0)
    
    Returns:
        String with detailed investment analysis
    """
    if future_age < start_age:
        return "Error: Future age must be greater than start age"
    
    stop_investing_age = stop_investing_age or future_age
    
    if stop_investing_age < start_age or stop_investing_age > future_age:
        return "Error: Stop investing age must be between start age and future age"
    
    total_years = future_age - start_age
    contributing_years = stop_investing_age - start_age
    growth_only_years = future_age - stop_investing_age if stop_investing_age else 0
    
    monthly_rate = annual_return / 100 / 12
    contributing_months = contributing_years * 12
    total_months = total_years * 12
    
    # Calculate future value of all components
    if monthly_rate > 0:
        # Future value of initial investment (grows for the entire period)
        initial_future_value = initial_investment * (1 + monthly_rate) ** total_months
        
        # Future value of monthly investments
        # First calculate value at stop_investing_age
        if contributing_months > 0:
            # PMT * (((1 + r)^n - 1) / r) * (1 + r)^t
            # where t is the remaining time after stopping contributions
            monthly_accumulated = monthly_investment * ((1 + monthly_rate) ** contributing_months - 1) / monthly_rate
            # Then let it grow until future_age
            monthly_future_value = monthly_accumulated * (1 + monthly_rate) ** (growth_only_years * 12)
        else:
            monthly_future_value = 0
    else:
        # Handle 0% return case
        initial_future_value = initial_investment
        monthly_future_value = monthly_investment * contributing_months
    
    # Calculate totals
    total_invested = initial_investment + (monthly_investment * contributing_months)
    future_value = initial_future_value + monthly_future_value
    total_returns = future_value - total_invested
    
    report = [
        f"\nInvestment Summary:",
        f"Initial investment: ${initial_investment:,.2f}",
        f"Monthly investment: ${monthly_investment:,.2f} (for {contributing_years} years)",
        f"Investment timeline:",
        f"- Start age: {start_age}",
        f"- Stop monthly investments: {stop_investing_age}",
        f"- Final calculation age: {future_age}",
        f"- Total growth period: {total_years} years",
        f"Annual return rate: {annual_return}%",
        f"\nResults:",
        f"Total invested: ${total_invested:,.2f}",
        f"Total returns: ${total_returns:,.2f}",
        f"Final amount: ${future_value:,.2f}"
    ]
    
    if contributing_years > 0 and growth_only_years > 0:
        report.extend([
            f"\nKey Milestones:",
            f"At age {stop_investing_age} (when monthly investments stop):",
            f"- Total invested: ${total_invested:,.2f}",
            f"- Continues growing for {growth_only_years} more years"
        ])
    
    return "\n".join(report)

if __name__ == "__main__":
    # Test parameters from user input
    result = calculate_compound_interest.run({
        "start_age": 20,
        "monthly_investment": 10000,
        "annual_return": 13.6,
        "future_age": 60,
        "stop_investing_age": 30,
        "initial_investment": 0
    })
    print(result)
