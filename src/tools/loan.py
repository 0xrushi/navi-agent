from typing import Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from langchain_core.tools import tool

# Results compared with https://maybe.co/tools/loan-calculator
@tool
def calculate_loan(
    loan_amount: float,
    loan_term_years: float,
    interest_rate: float,
    start_date: Optional[str] = None
) -> str:
    """
    Calculate loan payments, total interest, and generate amortization schedule.
    
    Args:
        loan_amount: Principal loan amount
        loan_term_years: Duration of loan in years
        interest_rate: Annual interest rate (percentage)
        start_date: Loan start date (YYYY-MM-DD format)
        
    Returns:
        String with detailed loan analysis and amortization schedule
    """
    if loan_amount <= 0 or loan_term_years <= 0 or interest_rate < 0:
        return "Error: Invalid loan parameters"

    # Convert annual rate to monthly
    monthly_rate = interest_rate / 100 / 12
    
    # Calculate total number of payments
    total_payments = int(loan_term_years * 12)
    
    # Calculate monthly payment
    if monthly_rate == 0:
        monthly_payment = loan_amount / total_payments
    else:
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**total_payments) / ((1 + monthly_rate)**total_payments - 1)
    
    # Set start date
    if start_date:
        current_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        current_date = date.today()
    
    # Initialize variables for amortization schedule
    remaining_balance = loan_amount
    total_interest = 0
    schedule = []
    
    # Generate amortization schedule
    for payment_num in range(1, total_payments + 1):
        # Calculate interest and principal for this payment
        interest_payment = remaining_balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        
        # Update running totals
        total_interest += interest_payment
        remaining_balance -= principal_payment
        
        # Record payment details
        schedule.append({
            'payment_num': payment_num,
            'date': current_date,
            'payment': monthly_payment,
            'principal': principal_payment,
            'interest': interest_payment,
            'balance': max(0, remaining_balance)
        })
        
        # Move to next month
        current_date = current_date + relativedelta(months=1)
    
    # Calculate final payoff date
    payoff_date = schedule[-1]['date']
    total_paid = loan_amount + total_interest
    
    # Generate report
    report = [
        f"\nLoan Analysis Summary",
        f"\nLoan Details:",
        f"Loan Amount: ${loan_amount:,.2f}",
        f"Interest Rate: {interest_rate}%",
        f"Loan Term: {loan_term_years} years",
        
        f"\nPayment Information:",
        f"Monthly Payment: ${monthly_payment:,.2f}",
        f"Total Number of Payments: {total_payments}",
        f"Start Date: {schedule[0]['date'].strftime('%B %d, %Y')}",
        f"Estimated Payoff Date: {payoff_date.strftime('%B %d, %Y')}",
        
        f"\nTotal Cost Breakdown:",
        f"Total Principal: ${loan_amount:,.2f}",
        f"Total Interest: ${total_interest:,.2f}",
        f"Total Amount Paid: ${total_paid:,.2f}",
        
        f"\nAmortization Schedule (First Year):"
    ]
    
    # Add first 12 payments detail
    for payment in schedule[:12]:
        report.append(
            f"Payment {payment['payment_num']} - {payment['date'].strftime('%B %Y')}: "
            f"Payment: ${payment['payment']:,.2f} "
            f"(Principal: ${payment['principal']:,.2f}, "
            f"Interest: ${payment['interest']:,.2f}), "
            f"Remaining Balance: ${payment['balance']:,.2f}"
        )
    
    # Add some key statistics
    interest_ratio = (total_interest / loan_amount * 100)
    report.extend([
        f"\nLoan Statistics:",
        f"Interest to Principal Ratio: {interest_ratio:.1f}%",
        f"Monthly Payment as Percentage of Loan: {(monthly_payment / loan_amount * 100):.2f}%",
        f"Total Interest as Percentage of Loan: {(total_interest / loan_amount * 100):.1f}%"
    ])
    
    return "\n".join(report)

if __name__ == "__main__":
    result = calculate_loan.run({
        "loan_amount": 300000,
        "loan_term_years": 30,
        "interest_rate": 6.5,
        "start_date": "2024-01-01"
    })
    print(result)