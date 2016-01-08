import csv
from a130 import *
data = []
for (i, date) in enumerate(dates):
    data.append({"date":dates[i], "index":indexes[i], "vol":volumes[i]})
with open('a130.csv', 'w') as csvfile:
    fieldnames = ['date','index','vol']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for (i, row) in enumerate(data):
        writer.writerow(row)
