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
    files = ["remove_nops.py", "local_dce.py", "trivial_global_optim.py", "local_value_numbering.py"]
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

if __name__ == "__main__":
    # Run the brench command
    run_brench_command()
    
    # Plot the results
    # missing_rows = plot_results()

    # run_individual_plots(missing_rows)

    # plot_missing()
    print("hello printing in main. Commands in this function can be run separately")