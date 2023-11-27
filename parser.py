import csv
import datetime

# Open the input text file for reading and the output CSV file for writing
with open('results.txt', 'r') as input_file, open('results.csv', 'w', newline='') as output_file:
    # Create a CSV writer object
    csv_writer = csv.writer(output_file)

    # Write the header to the CSV file
    csv_writer.writerow(['date', 'P1Name', 'P2Name', 'P1WinProb', 'P2WinProb'])

    # Read each line from the input text file
    date = ''
    P1Name = ''
    P2Name = ''
    P1WinProb = ''
    P2WinProb = ''
    for line in input_file:
        # Check if the line contains "pcsp"
        if '.pcsp' in line:
            data = line[45:-6].split('_')
            date = data[0]
            P1Name = data[1].replace('-', ' ')
            P2Name = data[2].replace('-', ' ')
        elif 'Valid with Probability' in line:
            data = line[87:-3].split(', ')
            P1WinProb = round((float(data[0]) + float(data[1])) / 2, 4)
            P2WinProb = round(1 - P1WinProb, 4)
            print([date, P1Name, P2Name, P1WinProb, P2WinProb])
            csv_writer.writerow([date, P1Name, P2Name, P1WinProb, P2WinProb])

print("CSV file 'results.csv' has been created.")
