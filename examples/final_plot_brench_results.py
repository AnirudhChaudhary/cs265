import subprocess
import matplotlib.pyplot as plt

# Run the brench command
# result = subprocess.run(['brench', 'brench.toml'], stdout=subprocess.PIPE)
# output = result.stdout.decode('utf-8')

# with open('brench_results.csv', 'w') as f:
#     f.write(output)

# Read the CSV file
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV file content
with open('brench_results.csv', 'r') as f:
    output = f.read()

# Parse the output into a list of dictionaries
data = []
for line in output.splitlines():
    if len(line.split(',')) != 3:
        continue
    test_file, run_name, num_instr = line.split(',')
    
    # Handle the "missing", "timeout", or "incorrect" case for num_instr
    if num_instr in ("incorrect", "timeout", "missing"):
        continue
    
    data.append({
        'test_file': test_file,
        'run_name': run_name,
        'num_instr': int(num_instr),
    })

# Group the data by test file
test_files = {}
for row in data:
    if row['test_file'] not in test_files:
        test_files[row['test_file']] = []
    test_files[row['test_file']].append(row)

# Set figure size
plt.figure(figsize=(12, 6))

# Create a list of test file names
test_file_names = list(test_files.keys())
x = np.arange(len(test_file_names))  # the label locations

# Calculate the differences (ssa - ref_ssa), and cap them at 2000
differences = []
for test_file in test_file_names:
    ssa_num = next((run['num_instr'] for run in test_files[test_file] if run['run_name'] == 'ssa'), None)
    ref_ssa_num = next((run['num_instr'] for run in test_files[test_file] if run['run_name'] == 'ref_ssa'), None)
    
    # Only calculate difference if both ssa and ref_ssa exist
    if ssa_num is not None and ref_ssa_num is not None:
        diff = ssa_num - ref_ssa_num
        
        # Cap the difference at 2000
        # if diff > 450:
        #     diff = 450
        
        differences.append(diff)
    else:
        differences.append(0)  # Default to 0 if there's missing data

min_diff = 0 
max_diff = 0
if differences:
    small = set(differences)
    small.remove(0)

    min_diff = min(small) 
    max_diff = max(differences) 

# 2. Count the number of files that had a difference (i.e., the difference is not zero)
num_files_with_difference = sum(1 for diff in differences if diff != 0)

# Print the results
print(f"Minimum Difference: {min_diff}")
print(f"Maximum Difference: {max_diff}")
print(f"Number of Files with a Difference: {num_files_with_difference}")
print(f"Total instructions saved: ", sum(differences))
# Plot the differences (capped at 2000)
plt.bar(x, differences, width=0.4, color='skyblue')

# Customize the plot
plt.xlabel('Test Files')
plt.ylabel('Difference in Number of Instructions (SSA - Ref_SSA)')
plt.title('Difference in Instructions Between SSA and Ref_SSA (Capped at 2000)')

# Set the x-axis tick labels to the test file names, rotating for readability
plt.xticks(x, test_file_names, rotation=90)

# Adjust layout to prevent label cut-off
plt.tight_layout()

# Show the plot
# plt.show()


