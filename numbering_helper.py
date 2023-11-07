import re

# Define a function to replace the pattern with incrementing values
def replace_with_incrementing_numbers(match):
    global current_number
    replacement = f"p{current_number}:"
    current_number += 1
    return replacement

# Open the input and output files
input_file = "LH_LH.txt"
output_file = "output.txt"

current_number = 0  # Initialize the current number

with open(input_file, "r") as infile, open(output_file, "w") as outfile:
    for line in infile:
        # Search for the pattern "pXX:" and replace with incrementing values
        modified_line = re.sub(r'p\d+:', replace_with_incrementing_numbers, line)
        outfile.write(modified_line)

print("Replacement completed. Output saved to 'output.txt'.")
