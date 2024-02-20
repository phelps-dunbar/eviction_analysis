import pandas as pd
import os

main_df = pd.read_csv('texes_eviction.csv')
# billed_dollars is target col

def get_total_billed_dollars(df):
    return df['billed_dollars'].sum()

def get_user_flat_fee(df):
    print("Enter a Flat Fee:")
    flat_fee = float(input())
    return flat_fee

def give_user_mean_billed_dollars(df):
    mean_billed_dollars = df['billed_dollars'].mean()
    print(f"The mean billed dollars is ${round(mean_billed_dollars, 2)}")
    return mean_billed_dollars

def give_user_median_billed_dollars(df):
    median_billed_dollars = df['billed_dollars'].median()
    print(f"The median billed dollars is ${round(median_billed_dollars, 2)}")
    return median_billed_dollars

def give_user_std_billed_dollars(df):
    std_billed_dollars = df['billed_dollars'].std()
    print(f"The standard deviation of billed dollars is ${round(std_billed_dollars, 2)}")
    return std_billed_dollars

def clear_command_line():
    os.system('cls' if os.name == 'nt' else 'clear')

def calculate_profit(flat_fee, total_billed_dollars):
    profit = (flat_fee * len(main_df)) - total_billed_dollars
    print(f"Your profit is ${round(profit, 2)} against {len(main_df)} Matters")
    return profit

def calc_number_of_losses_at_rate_with_avg(df, rate):
    number_of_losses = df[df['billed_dollars'] > rate].shape[0]
    avg_loss_value = df[df['billed_dollars'] < rate]['billed_dollars'].mean()
    print(f"The number of Matters where money is lost is {number_of_losses} at an average loss value of ${round(avg_loss_value, 2)}")
    return number_of_losses

def recommend_flatfee_given_profit_margin(df, margin):
    mean_billed_dollars = df['billed_dollars'].mean()
    additional_fee_for_margin = (margin / 100) * mean_billed_dollars
    flat_fee = mean_billed_dollars + additional_fee_for_margin
    print(f"Given a profit margin of {margin}%, we recommend a flat fee of ${round(flat_fee, 2)}")
    return flat_fee


def main():
    total_billed_dollars = get_total_billed_dollars(main_df)
    while True:
        clear_command_line()

        print("Simple Flat Fee Evaluation system")
        print("Here is the data:")
        mean_billed_dollars = give_user_mean_billed_dollars(main_df)
        median_billed_dollars = give_user_median_billed_dollars(main_df)
        std_billed_dollars = give_user_std_billed_dollars(main_df)
        
        print("Here are some options:")
        print("1. Enter a profit margin desired and we will recommend a flat fee")
        print("2. Enter a flat fee and we will calculate your profit")
        print("3. Exit")

        user_input = int(input())
        if user_input == 1:
            print("Enter a profit margin desired:")
            margin = float(input("%"))
            flat_fee = recommend_flatfee_given_profit_margin(main_df, margin)
            profit = calculate_profit(flat_fee, total_billed_dollars)
            number_of_losses = calc_number_of_losses_at_rate(main_df, flat_fee)

        elif user_input == 2:
            flat_fee = get_user_flat_fee(main_df)
            total_billed_dollars = get_total_billed_dollars(main_df)
            profit = calculate_profit(flat_fee, total_billed_dollars)
            number_of_losses = calc_number_of_losses_at_rate(main_df, flat_fee)

        elif user_input == 3:
            print("Goodbye")
            break
        else:
            print("Invalid input")
            return

        print("Again? (y/n)")
        user_input = input()
        if user_input.lower() != 'y':
            print("Goodbye")
            break
        else:
            continue

if __name__ == "__main__":
    main()