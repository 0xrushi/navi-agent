from typing import Optional
from datetime import datetime
from langchain_core.tools import tool
import math

# Results compared with https://maybe.co/tools/financial-freedom-calculator

@tool
def calculate_financial_freedom(
    current_savings: float,
    monthly_expenses: float,
    annual_growth_rate: float,
    expected_inflation_rate: float = 2.5,
    additional_monthly_savings: float = 0,
    withdrawal_strategy: str = "inflation_adjusted",
    target_end_balance: float = 0
) -> str:
    """
    Calculate how long savings will last given expenses and growth rate.
    
    Args:
        current_savings: Current savings/investment balance
        monthly_expenses: Monthly living expenses
        annual_growth_rate: Expected return on investments (percentage)
        expected_inflation_rate: Expected inflation rate (percentage)
        additional_monthly_savings: Optional ongoing monthly savings
        withdrawal_strategy: Either "inflation_adjusted" or "fixed"
        target_end_balance: Desired remaining balance at end (default 0)
        
    Returns:
        String with detailed financial independence analysis
    """
    if current_savings <= 0:
        return "Error: Current savings must be greater than zero."
    if monthly_expenses <= 0:
        return "Error: Monthly expenses must be greater than zero."
        
    # Initialize variables
    monthly_growth_rate = annual_growth_rate / 100 / 12

    monthly_inflation_rate = expected_inflation_rate / 100 / 12
    balance = current_savings
    months = 0
    yearly_projections = []
    current_year = datetime.now().year
    original_expenses = monthly_expenses

    # Calculate until money runs out or reaches target
    while balance > target_end_balance and months < 1200:  # Cap at 100 years
        if months % 12 == 0:
            yearly_projections.append({
                'year': current_year + (months // 12),
                'balance': balance,
                'monthly_expenses': monthly_expenses,
            })
            
        # Add any additional savings
        balance += additional_monthly_savings
        
        # Apply growth to remaining balance
        balance *= (1 + monthly_growth_rate)
        
        # Subtract monthly expenses
        balance -= monthly_expenses
        
        # Adjust expenses annually for inflation
        if withdrawal_strategy == "inflation_adjusted" and (months + 1) % 12 == 0:
            monthly_expenses *= (1 + expected_inflation_rate / 100)
        
        months += 1
        
        # Exit if balance drops below the target
        if balance <= target_end_balance:
            break
    
    # Calculate real (inflation-adjusted) final values
    years = months / 12
    inflation_factor = (1 + expected_inflation_rate / 100) ** years
    real_final_balance = balance / inflation_factor
    
    # Generate report
    report = [
        f"\nFinancial Freedom Analysis",
        f"\nInitial Information:",
        f"Current savings: ${current_savings:,.2f}",
        f"Original monthly expenses: ${original_expenses:,.2f}",
        f"Annual growth rate: {annual_growth_rate}%",
        f"Inflation rate: {expected_inflation_rate}%"
    ]
    
    if additional_monthly_savings > 0:
        report.append(f"Additional monthly savings: ${additional_monthly_savings:,.2f}")
    
    report.extend([
        f"\nProjected Results:",
        f"Your savings will last: {years:.1f} years ({months} months)",
        f"Final balance (nominal): ${balance:,.2f}",
        f"Final balance (real {current_year} dollars): ${real_final_balance:,.2f}",
        f"\nKey Milestones:"
    ])
    
    # Add milestone years (every 5 years, up to 8 milestones)
    step = max(1, len(yearly_projections) // 8)
    for projection in yearly_projections[::step]:
        report.append(
            f"Year {projection['year']}: "
            f"Balance: ${projection['balance']:,.2f}, "
            f"Monthly Expenses: ${projection['monthly_expenses']:,.2f}"
        )
    
    # Add recommendations
    safe_withdrawal_rate = 4.0  # Traditional 4% rule
    annual_expenses = original_expenses * 12
    target_nest_egg = annual_expenses * (100 / safe_withdrawal_rate)
    
    report.extend([
        f"\nFinancial Independence Insights:",
        f"Annual expenses: ${annual_expenses:,.2f}",
        f"Target nest egg for traditional 4% rule: ${target_nest_egg:,.2f}",
        f"Current savings ratio: {(current_savings / target_nest_egg * 100):.1f}% of target"
    ])
    
    return "\n".join(report)

if __name__ == "__main__":
    result = calculate_financial_freedom.run({
        "current_savings": 500000,
        "monthly_expenses": 4000,
        "annual_growth_rate": 7,
        "expected_inflation_rate": 2,
        "additional_monthly_savings": 0,
        "withdrawal_strategy": "fixed",
        "target_end_balance": 0
    })
    print(result)