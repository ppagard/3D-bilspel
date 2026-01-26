from typing import List, Dict, Tuple
import datetime


def calculate_loan(
    principal: float, rate: float, term_months: int
) -> Dict[str, object]:
    """
    Calculate loan amortization schedule.

    Args:
        principal: Loan amount (SEK)
        rate: Annual interest rate as decimal, e.g., 0.05 for 5%.
        term_months: Loan term in months.

    Raises:
        ValueError: If principal <= 0, rate < 0, or term_months <= 0.

    Returns:
        Dictionary with total payment, monthly payment, and amortization schedule.
    """
    # Guard against invalid inputs
    if principal <= 0:
        raise ValueError("Belopp måste vara större än 0")
    if rate < 0:
        raise ValueError("Ränta får inte vara negativ")
    if term_months <= 0:
        raise ValueError("Löptid måste vara större än 0")

    # Calculate monthly interest rate
    monthly_rate = rate / 12

    # Calculate monthly payment using standard loan formula
    if rate == 0:
        monthly_payment = principal / term_months
    else:
        monthly_payment = (
            principal
            * (monthly_rate * (1 + monthly_rate) ** term_months)
            / ((1 + monthly_rate) ** term_months - 1)
        )

    # Calculate total payment
    total_payment = monthly_payment * term_months

    # Generate amortization schedule
    schedule: List[Dict[str, float]] = []
    remaining_principal = principal

    for month in range(1, term_months + 1):
        # Calculate interest for this month
        interest_payment = remaining_principal * monthly_rate

        # Calculate principal payment (total - interest)
        principal_payment = monthly_payment - interest_payment

        # Update remaining principal
        remaining_principal -= principal_payment

        # Ensure we don't go negative due to rounding errors
        if remaining_principal < 0:
            remaining_principal = 0.0

        # Add to schedule
        schedule.append(
            {
                "month": month,
                "payment": monthly_payment,
                "interest": interest_payment,
                "principal": principal_payment,
                "remaining_principal": remaining_principal,
            }
        )

    # Format dates
    today = datetime.date.today()
    end_date = today.replace(
        year=today.year + (term_months // 12),
        month=(today.month + term_months) % 12 or 12,
        day=today.day,
    )

    return {
        "type": "loan",
        "amount": principal,
        "rate": rate,
        "term": term_months,
        "payment": monthly_payment,
        "total": total_payment,
        "schedule": schedule,
        "start_date": today.isoformat(),
        "end_date": end_date.isoformat(),
    }


def calculate_lease(
    lease_amount: float, rate: float, term_months: int, residual_value: float
) -> Dict[str, object]:
    """
    Calculate lease payment schedule.

    Args:
        lease_amount: Initial lease amount (SEK).
        rate: Annual interest rate as decimal, e.g., 0.05 for 5%.
        term_months: Lease term in months.
        residual_value: Expected value at end of lease (SEK).

    Raises:
        ValueError: If inputs are invalid – e.g., negative values, residual >= amount.

    Returns:
        Dictionary with total payment, monthly payment, and amortization schedule.
    """
    # Guard against invalid inputs
    if lease_amount <= 0:
        raise ValueError("Belopp måste vara större än 0")
    if rate < 0:
        raise ValueError("Ränta får inte vara negativ")
    if term_months <= 0:
        raise ValueError("Löptid måste vara större än 0")
    if residual_value < 0 or residual_value >= lease_amount:
        raise ValueError("Residualvärde måste vara positivt och mindre än beloppet")

    # Calculate monthly interest rate
    monthly_rate = rate / 12

    # Calculate total depreciation (lease amount - residual value)
    total_depreciation = lease_amount - residual_value

    # Calculate monthly depreciation payment
    if term_months == 0:
        monthly_depreciation = 0.0
    else:
        monthly_depreciation = total_depreciation / term_months

    # Calculate interest on the average lease balance
    avg_lease_balance = (lease_amount + residual_value) / 2
    monthly_interest = avg_lease_balance * monthly_rate

    # Calculate total monthly payment
    monthly_payment = monthly_depreciation + monthly_interest

    # Calculate total payment over lease term
    total_payment = monthly_payment * term_months

    # Generate amortization schedule
    schedule: List[Dict[str, float]] = []
    remaining_balance = lease_amount

    for month in range(1, term_months + 1):
        # Calculate interest payment
        interest_payment = remaining_balance * monthly_rate

        # Calculate depreciation (principal) payment
        principal_payment = monthly_depreciation

        # Update remaining balance
        remaining_balance -= principal_payment

        # Ensure we don't go negative due to rounding errors
        if remaining_balance < 0:
            remaining_balance = 0.0

        # Add to schedule
        schedule.append(
            {
                "month": month,
                "payment": monthly_payment,
                "interest": interest_payment,
                "principal": principal_payment,
                "remaining_balance": remaining_balance,
            }
        )

    # Format dates
    today = datetime.date.today()
    end_date = today.replace(
        year=today.year + (term_months // 12),
        month=(today.month + term_months) % 12 or 12,
        day=today.day,
    )

    return {
        "type": "lease",
        "amount": lease_amount,
        "rate": rate,
        "term": term_months,
        "residual_value": residual_value,
        "payment": monthly_payment,
        "total": total_payment,
        "schedule": schedule,
        "start_date": today.isoformat(),
        "end_date": end_date.isoformat(),
    }
