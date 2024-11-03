from typing import Optional
from datetime import datetime
from langchain_core.tools import tool

@tool
def calculate_401k_retirement(
    current_age: int,
    retirement_age: int,
    annual_salary: float,
    contribution_percentage: float,
    employer_match_percentage: float,
    employer_match_limit: float,
    annual_return: float,
    current_401k_balance: float = 0,
    salary_increase_rate: float = 2.0,
    expected_inflation_rate: float = 2.5,
    catch_up_contributions: bool = True,
    employer_match_dollar_limit: Optional[float] = None,
    employer_annual_max_match: Optional[float] = None
) -> str:
    """
    Calculate 401(k) retirement savings with comprehensive employer matching rules.
    
    Args:
        current_age: Current age of the individual
        retirement_age: Expected retirement age
        annual_salary: Current annual salary
        contribution_percentage: Percentage of salary contributed to 401(k)
        employer_match_percentage: Percentage of salary matched by employer
        employer_match_limit: Maximum percentage of salary employer will match
        annual_return: Expected average annual return (as percentage)
        current_401k_balance: Current 401(k) balance
        salary_increase_rate: Expected annual salary increase (percentage)
        expected_inflation_rate: Expected inflation rate (percentage)
        catch_up_contributions: Whether to include catch-up contributions after 50
        employer_match_dollar_limit: Maximum dollar amount employer will match per paycheck (optional)
        employer_annual_max_match: Maximum annual employer match (optional)
        
    Returns:
        String with detailed 401(k) analysis
    """
    if retirement_age <= current_age:
        return "Error: Retirement age must be greater than current age"
    
    # Initialize variables
    current_year = datetime.now().year
    years_until_retirement = retirement_age - current_age
    balance = current_401k_balance
    total_contributions = 0
    total_employer_match = 0
    yearly_totals = []
    
    # 2024 IRS contribution limits
    base_contribution_limit = 23000  # 2024 limit
    catch_up_amount = 7500  # 2024 catch-up limit for age 50+
    
    # Calculate monthly rates
    monthly_return = annual_return / 100 / 12
    monthly_salary_increase = salary_increase_rate / 100 / 12
    
    # Year-by-year calculation
    for year in range(years_until_retirement):
        age = current_age + year
        year_contributions = 0
        year_employer_match = 0
        remaining_annual_employer_match = employer_annual_max_match if employer_annual_max_match else float('inf')
        
        # Calculate annual contribution limit for this year
        annual_limit = base_contribution_limit
        if catch_up_contributions and age >= 50:
            annual_limit += catch_up_amount
        
        # Calculate monthly contribution and employer match
        annual_salary_for_year = annual_salary * (1 + salary_increase_rate/100)**year
        monthly_salary = annual_salary_for_year / 12
        monthly_contribution = (monthly_salary * contribution_percentage/100)
        
        for month in range(12):
            # Ensure contribution doesn't exceed annual limit
            remaining_limit = annual_limit - year_contributions
            monthly_actual_contribution = min(monthly_contribution, remaining_limit)
            
            if monthly_actual_contribution <= 0:
                continue
                
            # Calculate employer match with all limits applied
            # 1. Calculate base match based on percentage
            match_eligible_amount = min(monthly_salary/12 * employer_match_limit/100,
                                     monthly_actual_contribution)
            monthly_match = match_eligible_amount * (employer_match_percentage/100)
            
            # 2. Apply per-paycheck dollar limit if specified
            if employer_match_dollar_limit:
                monthly_match = min(monthly_match, employer_match_dollar_limit)
            
            # 3. Apply remaining annual employer match limit
            monthly_match = min(monthly_match, remaining_annual_employer_match)
            remaining_annual_employer_match -= monthly_match
            
            # Update monthly totals
            year_contributions += monthly_actual_contribution
            year_employer_match += monthly_match
            
            # Apply monthly growth
            balance = (balance + monthly_actual_contribution + monthly_match) * (1 + monthly_return)
        
        # Update running totals
        total_contributions += year_contributions
        total_employer_match += year_employer_match
        
        # Store yearly totals
        yearly_totals.append({
            'age': age,
            'year': current_year + year,
            'salary': monthly_salary * 12,
            'contribution': year_contributions,
            'employer_match': year_employer_match,
            'year_end_balance': balance
        })
    
    # Calculate real (inflation-adjusted) values
    inflation_factor = (1 + expected_inflation_rate/100)**years_until_retirement
    real_final_balance = balance / inflation_factor
    
    # Generate report
    report = [
        f"\n401(k) Retirement Analysis",
        f"\nInitial Information:",
        f"Current age: {current_age}",
        f"Retirement age: {retirement_age}",
        f"Starting salary: ${annual_salary:,.2f}",
        f"Current 401(k) balance: ${current_401k_balance:,.2f}",
        f"\nContribution Details:",
        f"Your contribution: {contribution_percentage}% of salary",
        f"Employer match: {employer_match_percentage}% up to {employer_match_limit}% of salary"
    ]
    
    if employer_match_dollar_limit:
        report.append(f"Employer match dollar limit per paycheck: ${employer_match_dollar_limit:,.2f}")
    if employer_annual_max_match:
        report.append(f"Employer annual maximum match: ${employer_annual_max_match:,.2f}")
        
    report.extend([
        f"Expected annual return: {annual_return}%",
        f"Expected salary increase: {salary_increase_rate}%",
        f"\nProjected Results:",
        f"Total personal contributions: ${total_contributions:,.2f}",
        f"Total employer match: ${total_employer_match:,.2f}",
        f"Total contributions: ${(total_contributions + total_employer_match):,.2f}",
        f"Final balance (nominal): ${balance:,.2f}",
        f"Final balance (real 2024 dollars): ${real_final_balance:,.2f}",
        f"\nKey Milestones:"
    ])
    
    # Add milestone years (every 5 years)
    for total in yearly_totals[::5]:
        report.append(
            f"Age {total['age']} ({total['year']}): "
            f"Balance: ${total['year_end_balance']:,.2f}, "
            f"Salary: ${total['salary']:,.2f}"
        )
    
    return "\n".join(report)

if __name__ == "__main__":
    
    result = calculate_401k_retirement.run({
        "current_age": 30,
        "retirement_age": 65,
        "annual_salary": 100000,
        "contribution_percentage": 10,
        "employer_match_percentage": 100,
        "employer_match_limit": 6,
        "annual_return": 7,
        "current_401k_balance": 50000,
        "salary_increase_rate": 2.0,
        "expected_inflation_rate": 2.5,
        "catch_up_contributions": True,
        "employer_match_dollar_limit": 500,
        "employer_annual_max_match": 5000 
    })
    print(result)