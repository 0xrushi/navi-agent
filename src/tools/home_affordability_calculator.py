from typing import Optional
from datetime import datetime
from langchain_core.tools import tool
from enum import Enum

class AffordabilityRisk(Enum):
    COMFORTABLE = "You're good"
    CAUTIOUS = "Okay but use caution"
    RISKY = "Risky don't do it"
    EXTREME = "Good luck with that"

# Results compared with https://maybe.co/tools/home-affordability-calculator
@tool
def calculate_home_affordability(
    annual_income: float,
    down_payment: float,
    loan_term_years: int,
    interest_rate: float,
    monthly_debt: float,
    monthly_hoa_pmi: float = 0,
    property_tax_rate: float = 1.1,
    home_insurance_rate: float = 0.5,
    desired_home_price: Optional[float] = None,
    max_dti_ratio: float = 43,
    front_end_dti_ratio: float = 28,
    min_down_payment_percent: float = 3.5
) -> str:
    """
    Calculate home affordability with risk levels based on income and debt ratios.
    
    Args:
        annual_income: Annual pre-tax income
        down_payment: Available down payment
        loan_term_years: Loan duration in years
        interest_rate: Annual interest rate (percentage)
        monthly_debt: Monthly debt payments (car, credit cards, etc.)
        monthly_hoa_pmi: Monthly HOA fees and PMI (optional)
        property_tax_rate: Annual property tax rate (percentage)
        home_insurance_rate: Annual home insurance rate (percentage)
        desired_home_price: Optional desired home price to analyze
        max_dti_ratio: Maximum debt-to-income ratio (percentage)
        front_end_dti_ratio: Maximum housing expense ratio (percentage)
        min_down_payment_percent: Minimum required down payment (percentage)
        
    Returns:
        String with detailed home affordability analysis and risk levels
    """
    if annual_income <= 0 or down_payment < 0:
        return "Error: Income must be positive and down payment cannot be negative"
    
    # Calculate monthly income
    monthly_income = annual_income / 12
    
    def calculate_monthly_payment(price: float) -> dict:
        """Calculate all monthly costs for a given home price"""
        loan_amount = price - down_payment
        
        # Calculate monthly mortgage payment (P&I)
        monthly_rate = (interest_rate / 100) / 12
        num_payments = loan_term_years * 12
        if monthly_rate == 0:
            monthly_mortgage = loan_amount / num_payments
        else:
            monthly_mortgage = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        
        # Calculate other monthly costs
        monthly_property_tax = (price * (property_tax_rate / 100)) / 12
        monthly_insurance = (price * (home_insurance_rate / 100)) / 12
        
        # PMI (if down payment < 20%)
        pmi = 0
        if (down_payment / price) < 0.2:
            pmi = (loan_amount * 0.01) / 12
        
        total_monthly = (monthly_mortgage + monthly_property_tax + monthly_insurance + 
                        monthly_hoa_pmi + pmi)
        
        total_debt_payment = total_monthly + monthly_debt
        
        return {
            'monthly_mortgage': monthly_mortgage,
            'monthly_property_tax': monthly_property_tax,
            'monthly_insurance': monthly_insurance,
            'monthly_hoa_pmi': monthly_hoa_pmi,
            'monthly_pmi': pmi,
            'total_monthly': total_monthly,
            'total_debt_payment': total_debt_payment,
            'front_end_ratio': (total_monthly / monthly_income) * 100,
            'back_end_ratio': (total_debt_payment / monthly_income) * 100
        }
    
    # Calculate price ranges based on different DTI thresholds
    def find_max_price(target_dti: float) -> float:
        low = 0
        high = (annual_income * 5)
        max_price = 0
        
        while high - low > 1000:
            mid = (high + low) / 2
            payments = calculate_monthly_payment(mid)
            
            if payments['back_end_ratio'] <= target_dti:
                max_price = mid
                low = mid
            else:
                high = mid
        
        return max_price

    # Calculate different affordability ranges
    comfortable_max = find_max_price(front_end_dti_ratio)
    cautious_max = find_max_price(35)
    risky_max = find_max_price(max_dti_ratio)
    
    # Determine risk level for desired price
    def get_risk_level(price: float) -> AffordabilityRisk:
        if price <= comfortable_max:
            return AffordabilityRisk.COMFORTABLE
        elif price <= cautious_max:
            return AffordabilityRisk.CAUTIOUS
        elif price <= risky_max:
            return AffordabilityRisk.RISKY
        else:
            return AffordabilityRisk.EXTREME
    
    # Calculate metrics for desired price or maximum comfortable price
    analysis_price = desired_home_price if desired_home_price else comfortable_max
    payments = calculate_monthly_payment(analysis_price)
    risk_level = get_risk_level(analysis_price)
    
    # Generate report
    report = [
        f"\nHome Affordability Analysis",
        f"\nAffordability Ranges:",
        f"Up to ${comfortable_max:,.2f} - {AffordabilityRisk.COMFORTABLE.value}",
        f"${comfortable_max:,.2f}-${cautious_max:,.2f} - {AffordabilityRisk.CAUTIOUS.value}",
        f"${cautious_max:,.2f}-${risky_max:,.2f} - {AffordabilityRisk.RISKY.value}",
        f"Over ${risky_max:,.2f} - {AffordabilityRisk.EXTREME.value}",
        
        f"\nAnalysis for {'Desired' if desired_home_price else 'Maximum Comfortable'} Price: ${analysis_price:,.2f}",
        f"Risk Level: {risk_level.value}",
        
        f"\nMonthly Payment Breakdown:",
        f"Principal & Interest: ${payments['monthly_mortgage']:,.2f}",
        f"Property Tax: ${payments['monthly_property_tax']:,.2f}",
        f"Home Insurance: ${payments['monthly_insurance']:,.2f}",
        f"HOA/PMI: ${payments['monthly_hoa_pmi']:,.2f}",
        f"Additional PMI: ${payments['monthly_pmi']:,.2f}",
        f"Total Monthly Housing: ${payments['total_monthly']:,.2f}",
        f"Total Monthly with Debt: ${payments['total_debt_payment']:,.2f}",
        
        f"\nAffordability Metrics:",
        f"Housing Expense Ratio: {payments['front_end_ratio']:.1f}% (Target: {front_end_dti_ratio}%)",
        f"Debt-to-Income Ratio: {payments['back_end_ratio']:.1f}% (Max: {max_dti_ratio}%)"
    ]
    
    down_payment_percent = (down_payment / analysis_price) * 100
    if down_payment_percent < 20:
        report.append(f"\nNote: Down payment ({down_payment_percent:.1f}%) is below 20% - PMI required")
    
    if down_payment_percent < min_down_payment_percent:
        report.append(f"\nWarning: Down payment is below minimum required ({min_down_payment_percent}%)")
    
    if payments['back_end_ratio'] > max_dti_ratio:
        report.append(f"\nWarning: Debt-to-income ratio exceeds recommended maximum")
    
    return "\n".join(report)

if __name__ == "__main__":
    result = calculate_home_affordability.run({
        "annual_income": 100000,
        "down_payment": 50000,
        "loan_term_years": 30,
        "interest_rate": 1,
        "monthly_debt": 500,
        "monthly_hoa_pmi": 200,
        "desired_home_price": 700000,
        "property_tax_rate": 1.1,
        "home_insurance_rate": 0.5,
        "max_dti_ratio": 43,
        "front_end_dti_ratio": 28,
        "min_down_payment_percent": 3.5
    })
    print(result)