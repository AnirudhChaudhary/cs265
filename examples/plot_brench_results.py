import subprocess
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Step 1: Run the command 'brench brench.toml > results.csv' using subprocess
def run_brench_command():
    command = 'brench brench.toml -p > results.csv'
    
    try:
        subprocess.run(command, shell=True, check=True)
        print("Command executed successfully and results saved to results.csv.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running command: {e}")

# Step 2: Read results.csv, handle missing values, and plot the data from bottom-up
def plot_results():
    # Load the CSV data
    try:
        df = pd.read_csv('results.csv', header=None, names=["example", "optimization", "score"], skiprows=1)

        missing_rows = df[df['score'] == 'missing']["example"].unique()

        # # Replace 'missing' values with 0
        # df['score'] = df['score'].replace('missing', 0)
        # df['score'] = df['score'].replace('incorrect', -1)

        # # Convert score column to numeric (in case 'missing' was present as a string)
        # df['score'] = pd.to_numeric(df['score'])

        # # Create a horizontal bar plot (for bottom-up effect)
        # plt.figure(figsize=(10, 6))
        # sns.barplot(data=df, x="score", y="example", hue="optimization", palette="muted", orient='h')

        # # Add labels and title for clarity
        # plt.title('Performance of Examples with Different Optimizations')
        # plt.xlabel('Scores')
        # plt.ylabel('Examples')

        # # Display the plot
        # # plt.savefig("saved.png")
        # plt.show()
    except FileNotFoundError:
        print("Error: results.csv not found. Ensure the command was executed successfully and results.csv was generated.")
    
    return missing_rows

def run_individual_plots(inputs):
    files = ["remove_nops.py", "cnst_prop.py"]
    benchmark_dir = '../../benchmarks/ani_benchmarks/task1/'
    for file_name in inputs:
        final_command =  f'cat {benchmark_dir + file_name}.bril | bril2json | brili -p '
        for script_name in files:
            command = f'&& cat {benchmark_dir + file_name}.bril | bril2json | python3 {script_name} | brili -p '
            final_command += command

        # print(final_command)
        try:
            subprocess.run(final_command, shell=True, check=True)
            print(f"Ran {file_name}")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running command: {e}")


def plot_missing():
    """
    Though a little manual made, this is a file that is used for individually printing out cases that did not work by brench.
    """
    data = {
        "sum_mul": [7,7,6,6,6],
        "double-pass": [6,6,4,4,6],
        "combo": [6,6,4,5,6],
        "ani_ex_multi" : [16,16,16,16,12],
        "reassign-dkp" : [3,3,2,3,3]
    }
    runs = ["base", "remove_nops", "local_dce", "trivial_global_optim", "local_value_numbering"]

    # Convert the dictionary to a pandas DataFrame
    df = pd.DataFrame(data, index=runs).T
    # Create a bar plot for each test and its runs
    plt.figure(figsize=(10, 6))
    df.plot(kind="bar", figsize=(10, 6), colormap="viridis")

    # Add labels and title
    plt.title('Number of Instructions for Different Runs per Test')
    plt.xlabel('Tests')
    plt.ylabel('Number of Instructions')

    # Display the plot
    plt.show()

import os
import subprocess
import csv
import re

# The directory where .bril files are stored
BENCHMARKS_DIR = '../benchmarks'

# Command template to run bril2json and cnst_prop.py
CMD_TEMPLATE = 'cat {file} | bril2json | python3 cnst_prop.py'

# Regular expression to extract the number of arguments (adapt as necessary)
ARGS_REGEX = r'total_args: (\d+)'

# CSV file output path
CSV_OUTPUT = 'cnst_prop_args_count.csv'


def find_bril_files(benchmarks_dir):
    """Recursively find all .bril files in the benchmarks directory."""
    bril_files = []
    for root, dirs, files in os.walk(benchmarks_dir):
        for file in files:
            if file.endswith('.bril'):
                bril_files.append(os.path.join(root, file))
    return bril_files


def run_command(cmd):
    """Run a shell command and return the output."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout


def extract_arguments(output):
    """Extract the number of arguments from the output using regex."""
    match = re.search(ARGS_REGEX, output)
    if match:
        return int(match.group(1))
    return None


def write_to_csv(data, csv_output):
    """Write the data to a CSV file."""
    with open(csv_output, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['File', 'Number of Arguments'])
        for file_name, args in data:
            writer.writerow([file_name, args])


def main():
    # Step 1: Get all the .bril files
    bril_files = find_bril_files(BENCHMARKS_DIR)

    # Store results for the CSV
    csv_data = []

    # Step 2: For each file, run bril2json and cnst_prop.py, and extract the number of arguments
    for bril_file in bril_files:
        # Build the command
        cmd = CMD_TEMPLATE.format(file=bril_file)
        
        # Run the command and capture the output
        output = run_command(cmd)


        # Step 3: Extract the number of arguments
        # num_args = extract_arguments(output)
        # If arguments were found, store the result
        if output is not None:
            file_name = os.path.basename(bril_file)
            csv_data.append((file_name, output))

    # Step 4: Write the results to a CSV file
    write_to_csv(csv_data, CSV_OUTPUT)
    print(f"Results written to {CSV_OUTPUT}")

import pandas as pd

def count_total_arguments(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Sum the "Number of Arguments" column
    total_arguments = df['Number of Arguments'].sum()
    
    return total_arguments

import pandas as pd
import re

def clean_result(value):
    # Remove non-numeric parts from the result using regex
    cleaned_value = re.sub(r'[^\d]', '', value)
    return int(cleaned_value) if cleaned_value else 0  # Convert to integer or 0 if empty

def aggregate_results(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Apply cleaning to the 'result' column to remove non-numeric characters
    df['cleaned_result'] = df['result'].apply(clean_result)
    
    # Group by the 'run' column and sum the cleaned 'result' column
    aggregated_results = df.groupby('run')['cleaned_result'].sum()
    
    return aggregated_results

if __name__ == "__main__":
    file_path = 'results.csv'  # Path to your CSV file
    aggregated_results = aggregate_results(file_path)
    
    # Print the aggregated sum for each run type
    print(aggregated_results)





# if __name__ == "__main__":
#     run_brench_command()
    # main()
    # import pandas as pd
    # import matplotlib.pyplot as plt

    # # Paths to your CSV files
    # csv_file_1 = 'baseline_args_count.csv'  # First CSV file
    # csv_file_2 = 'cnst_prop_args_count.csv'  # Second CSV file

    # # Read the CSVs into DataFrames
    # df1 = pd.read_csv(csv_file_1)
    # df2 = pd.read_csv(csv_file_2)

    # # Rename columns for clarity (e.g., 'Number of Arguments' from each CSV)
    # df1.columns = ['File', 'Args_1']
    # df2.columns = ['File', 'Args_2']

    # # Merge the DataFrames on the 'File' column
    # merged_df = pd.merge(df1, df2, on='File')

    # # Calculate the difference between the second columns (Args_1 and Args_2)
    # merged_df['Difference'] = merged_df['Args_1'] - merged_df['Args_2']

    # # Plot the differences
    # plt.figure(figsize=(10, 6))
    # plt.bar(merged_df['File'], merged_df['Difference'], color='skyblue')
    # plt.xticks(rotation=90)  # Rotate file names for better readability
    # plt.xlabel('File Name')
    # plt.ylabel('Difference in Arguments')
    # plt.title('Difference in Number of Arguments Between Two CSVs')
    # plt.tight_layout()  # Adjust layout to prevent label cut-off
    # plt.show()








    # Run the brench command
    # run_brench_command()
    
    # Plot the results
    # missing_rows = plot_results()

    # run_individual_plots(missing_rows)

    # plot_missing()
    # print("hello printing in main. Commands in this function can be run separately")