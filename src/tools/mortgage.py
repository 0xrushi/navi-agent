from typing import Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from dataclasses import dataclass
from langchain_core.tools import tool

@dataclass
class MortgageResults:
    interest_savings: float
    time_saved_years: int
    time_saved_months: int
    total_interest_original: float
    total_interest_with_extra: float
    total_payments_original: float
    total_payments_with_extra: float
    original_payoff_date: date
    new_payoff_date: date
    investment_balance: float
    net_difference: float
    monthly_payment: float

# Results compared with https://maybe.co/tools/early-mortgage-payoff-calculator     
@tool
def calculate_mortgage_comparison(
    loan_amount: float,
    original_term_years: int,
    years_left: float,
    interest_rate: float,
    extra_payment: float,
    investment_return: float,
    start_date: Optional[str] = None
) -> str:
    """
    Calculate the impact of extra mortgage payments vs investing the difference
    
    Args:
        loan_amount: Original loan amount
        original_term_years: Original loan term in years
        years_left: Years remaining on loan
        interest_rate: Annual interest rate (percentage)
        extra_payment: Additional monthly payment
        investment_return: Expected annual investment return (percentage)
        start_date: Start date for calculations (optional, defaults to current date)
        
    Returns:
        String with detailed mortgage analysis
    """
    if loan_amount <= 0 or original_term_years <= 0 or years_left <= 0:
        return "Error: Loan amount and terms must be greater than zero"
    
    # Initialize variables
    monthly_rate = interest_rate / 100 / 12
    investment_monthly_rate = investment_return / 100 / 12
    total_months_original = int(years_left * 12)
    
    # Calculate base monthly payment (P&I only)
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**(original_term_years * 12)) / ((1 + monthly_rate)**(original_term_years * 12) - 1)
    
    # Set start date
    if start_date:
        current_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        current_date = datetime.now().date()
    
    # Calculate original amortization
    balance = loan_amount
    total_interest_original = 0
    original_payoff_date = current_date + relativedelta(months=total_months_original)
    
    for _ in range(total_months_original):
        interest = balance * monthly_rate
        principal = monthly_payment - interest
        total_interest_original += interest
        balance -= principal
    
    # Calculate new amortization with extra payments
    balance = loan_amount
    total_interest_with_extra = 0
    months_with_extra = 0
    investment_balance = 0
    
    while balance > 0 and months_with_extra < total_months_original:
        interest = balance * monthly_rate
        total_payment = monthly_payment + extra_payment
        principal = min(total_payment - interest, balance)
        
        total_interest_with_extra += interest
        balance -= principal
        months_with_extra += 1
        
        # Calculate investment returns if the extra payment was invested instead
        investment_balance = (investment_balance + extra_payment) * (1 + investment_monthly_rate)
    
    # Calculate results
    new_payoff_date = current_date + relativedelta(months=months_with_extra)
    time_saved = relativedelta(original_payoff_date, new_payoff_date)
    interest_savings = total_interest_original - total_interest_with_extra
    net_difference = investment_balance - interest_savings
    
    results = MortgageResults(
        interest_savings=interest_savings,
        time_saved_years=time_saved.years,
        time_saved_months=time_saved.months,
        total_interest_original=total_interest_original,
        total_interest_with_extra=total_interest_with_extra,
        total_payments_original=loan_amount + total_interest_original,
        total_payments_with_extra=loan_amount + total_interest_with_extra,
        original_payoff_date=original_payoff_date,
        new_payoff_date=new_payoff_date,
        investment_balance=investment_balance,
        net_difference=net_difference,
        monthly_payment=monthly_payment
    )
    
    # Generate report
    report = [
        f"\nMortgage Payoff Analysis",
        f"\nLoan Details:",
        f"Loan amount: ${loan_amount:,.2f}",
        f"Original term: {original_term_years} years",
        f"Years remaining: {years_left} years",
        f"Interest rate: {interest_rate}%",
        f"Monthly payment (P&I): ${monthly_payment:.2f}",
        f"Extra monthly payment: ${extra_payment:.2f}",
        f"\nComparison Results:",
        f"Interest savings: ${results.interest_savings:,.2f}",
        f"Time saved: {results.time_saved_years} years, {results.time_saved_months} months",
        f"\nOriginal Mortgage:",
        f"Total interest: ${results.total_interest_original:,.2f}",
        f"Total payments: ${results.total_payments_original:,.2f}",
        f"Payoff date: {results.original_payoff_date.strftime('%B %Y')}",
        f"\nWith Extra Payments:",
        f"Total interest: ${results.total_interest_with_extra:,.2f}",
        f"Total payments: ${results.total_payments_with_extra:,.2f}",
        f"Payoff date: {results.new_payoff_date.strftime('%B %Y')}",
        f"\nInvestment Comparison:",
        f"Investment return rate: {investment_return}%",
        f"Investment account balance: ${results.investment_balance:,.2f}",
        f"Net difference (Investment Value - Interest Savings): ${results.net_difference:,.2f}",
        f"\nRecommendation:",
    ]
    
    if results.net_difference > 0:
        report.append(
            "Investing the extra payments could potentially earn you more money "
            f"(${abs(results.net_difference):,.2f} more) than paying off the mortgage early."
        )
    else:
        report.append(
            "Paying off the mortgage early could potentially save you more money "
            f"(${abs(results.net_difference):,.2f} more) than investing the extra payments."
        )
    
    return "\n".join(report)

if __name__ == "__main__":
    # Example usage
    result = calculate_mortgage_comparison.run({
        "loan_amount": 500000,
        "original_term_years": 30,
        "years_left": 30,
        "interest_rate": 6.72,
        "extra_payment": 500,
        "investment_return": 4.0
    })
    print(result)