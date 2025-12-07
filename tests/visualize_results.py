import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt

def create_graphs(csv_file: str):
    """
    Reads a CSV file with temperature test results and generates metric graphs.
    """
    if not os.path.exists(csv_file):
        print(f"❌ Error: The file '{csv_file}' was not found.")
        return

    # Read the data
    df = pd.read_csv(csv_file)

    # Ensure temperature is treated as a categorical variable for plotting
    df['temperature'] = df['temperature'].astype(str)

    # Create a figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    fig.suptitle('Analysis of Code Review Generation by Temperature', fontsize=16)

    # --- Plot 1: Number of Review Comments ---
    ax1.bar(df['temperature'], df['num_review_comments'], color='skyblue')
    ax1.set_title('Number of Review Comments vs. Temperature')
    ax1.set_xlabel('Temperature Setting')
    ax1.set_ylabel('Total Review Comments Found')
    ax1.grid(axis='y', linestyle='--', alpha=0.7)

    # --- Plot 2: Duration in Seconds ---
    ax2.bar(df['temperature'], df['duration_seconds'], color='salmon')
    ax2.set_title('Test Duration vs. Temperature')
    ax2.set_xlabel('Temperature Setting')
    ax2.set_ylabel('Duration (seconds)')
    ax2.grid(axis='y', linestyle='--', alpha=0.7)

    # Save the figure
    output_filename = os.path.splitext(csv_file)[0] + '.png'
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to make room for suptitle
    plt.savefig(output_filename)

    print(f"✅ Graphs saved successfully to {output_filename}")

def main():
    parser = argparse.ArgumentParser(description="Visualize temperature test results from a CSV file.")
    parser.add_argument("csv_file", help="The path to the input CSV file containing test results.")
    args = parser.parse_args()
    create_graphs(args.csv_file)

if __name__ == "__main__":
    main()