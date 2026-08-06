"""Simple command-line EMI calculator."""


def calculate_emi(principal, annual_rate, tenure_months):
    monthly_rate = annual_rate / 12 / 100

    if monthly_rate == 0:
        emi = principal / tenure_months
        return emi, principal, 0

    factor = (1 + monthly_rate) ** tenure_months
    emi = (principal * monthly_rate * factor) / (factor - 1)
    total_payment = emi * tenure_months
    total_interest = total_payment - principal

    return emi, total_payment, total_interest


def get_positive_number(prompt):
    while True:
        try:
            value = float(input(prompt))
            if value <= 0:
                print("Please enter a value greater than 0.")
                continue
            return value
        except ValueError:
            print("Please enter a valid number.")


def main():
    print("=== EMI Calculator ===")
    principal = get_positive_number("Enter principal amount: ")
    rate = get_positive_number("Enter annual interest rate (%): ")
    years = get_positive_number("Enter loan duration (in years): ")
    tenure_months = round(years * 12)

    emi, total_payment, total_interest = calculate_emi(principal, rate, tenure_months)

    print("\n--- Results ---")
    print(f"Monthly EMI     : {emi:,.2f}")
    print(f"Total Payment   : {total_payment:,.2f}")
    print(f"Total Interest  : {total_interest:,.2f}")


if __name__ == "__main__":
    main()
