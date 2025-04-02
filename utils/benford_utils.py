import numpy as np
import pandas as pd

BENFORD_PROBS = np.array([0.301, 0.176, 0.125, 0.097, 0.079, 0.067, 0.058, 0.051, 0.046])

def first_digit(series):
    def get_first_non_zero_digit(number):
        num_str = str(number).replace(',', '')
        for char in num_str:
            if char.isdigit() and char != '0':
                return int(char)
        return np.nan
    return series.apply(get_first_non_zero_digit).dropna().astype(int)

def chi_square_test(observed_counts, expected_counts):
    return np.sum(((observed_counts - expected_counts) ** 2) / expected_counts)

def apply_benford_law(df):
    chi_stats = []
    processed_columns = []

    for column in df.select_dtypes(include=[np.number]).columns:
        if column == 'Label':
            continue

        first_digits = first_digit(df[column].dropna())
        if first_digits.empty:
            continue

        total_values = len(first_digits)
        observed_counts = [(first_digits == digit).sum() for digit in range(1, 10)]
        expected_counts = BENFORD_PROBS * total_values
        chi_square_statistic = chi_square_test(np.array(observed_counts), expected_counts)

        chi_stats.append(chi_square_statistic)
        processed_columns.append(column)

    if not chi_stats:
        return {"error": "No numeric columns available for feature selection."}

    chi_stats_df = pd.DataFrame({'Features': processed_columns, 'Chi-Square': chi_stats})
    mean_threshold = chi_stats_df['Chi-Square'].mean()
    median_threshold = chi_stats_df['Chi-Square'].median()

    selected_features = chi_stats_df[chi_stats_df['Chi-Square'] >= median_threshold]['Features'].tolist()
    if not selected_features:
        return {"error": "No features selected based on the median threshold."}

    selected_features.append('Label')  # Ensure label is included

    return {
        "mean_threshold": mean_threshold,
        "median_threshold": median_threshold,
        "selected_features": selected_features,
        "chi_stats": chi_stats_df.to_dict(orient="records")
    }