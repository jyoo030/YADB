import pandas as pd
from urllib.request import urlopen
import json
import csv


class csvDownloader():
	def __init__(self):
		pass	

	def find_data(self, countryName):
		

		df = pd.read_csv(url)
		global myDict 
		myDict = df.to_dict()

		global x
		x = list(myDict['Name'].keys())[list(myDict['Name'].values()).index(countryName)]
		
		message = "\n"
		for value in myDict:
			
			message += str(f"{value}: {myDict[f'{value}'][x]} \n")
		
		return str(message)

	def country_list(self):
		df = pd.read_csv(url)
		global myDict 
		myDict = df.to_dict()

		clist = []
		for value in myDict['Name'].values():
			clist.append(str(f"{value}"))
		
		sorted_clist = sorted(clist, key=str.lower)
		
		
		return sorted_clist

url = r"https://covid19.who.int/WHO-COVID-19-global-table-data.csv"
