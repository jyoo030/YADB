import pandas as pd
from urllib.request import urlopen
import json
import csv


class csvDownloader():
	def __init__(self):
		pass	

	def find_data(self, countryName):
		
		df = pd.read_csv(url)
		myDict = df.to_dict()

		x = list(myDict['Name'].keys())[list(myDict['Name'].values()).index(countryName)]
		
		message = "\n"
		for value in myDict:
			print(value, myDict[f'{value}'][x])
			message += str(f"{value}: {myDict[f'{value}'][x]} \n")
		
		return str(message)

url = r"https://covid19.who.int/WHO-COVID-19-global-table-data.csv"
