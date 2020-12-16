import pandas as pd
from urllib.request import urlopen
import json
import csv


class csvDownloader():
	def __init__(self):
		pass	

	def find_data(self, input, message):
		data = pd.read_csv(csvfile)
		data.to_json(jsonfile)

		df = pd.read_csv(csvfile)
		myDict = df.to_dict()	


		x = list(myDict['Name'].keys())[list(myDict['Name'].values()).index(input)]
		message = "\n"
		for value in myDict:
			print(value, myDict[f'{value}'][x])
			message += f"{value}:{myDict[f'{value}'][x]}"
		return message

url = r"https://covid19.who.int/WHO-COVID-19-global-table-data.csv"
csvfile = r'/Users/roryzhang/Downloads/covid.csv'
jsonfile = r'/Users/roryzhang/YADB/Data Bases/coviddata.json'
