from requests_html import HTMLSession
from bs4 import BeautifulSoup
import random as rand

rand_num = f'{rand.randrange(1,188):03}'

url = r"https://www.madtakes.com/libs/num.html"

url = url.replace('num', rand_num)
print(url)
session = HTMLSession()
res = session.get(url)
soup = BeautifulSoup(res.content, 'html.parser')

user_inputs = soup.find(style='margin-bottom: 20px')

text_chunk = soup.find(bgcolor='#d0d0d0')
for i in text_chunk.select('br'):
    i.replace_with('\n')
string = str(text_chunk.text).strip()

def countWord(word):

    numWord = 0
    for i in range(1, len(word)-1):
        if word[i-1:i+3] == 'WORD':
            numWord += 1
    return numWord

input_list = []
inputs = user_inputs.find_all('td', align='right')
for word in inputs:
    input_list.append(word.text)

id_list = []
num_words = countWord(string)
for i in range(1, num_words+1):
    ids = str(user_inputs.find(id=f"w{i}"))
    if 'hidden' in ids:
        index = ids.find('value')
        id_num = ids[index+9]
    else:
        index = ids.find('id')
        id_num = ids[index+5]
    id_list.append(id_num)

word_dict = {}
counter = 0
for i in range(num_words):
    num = id_list[i]
    if int(num) in word_dict.keys():
        word_dict[i+1] = word_dict[int(num)]
    elif counter<len(input_list):
        word_dict[i+1] = input(f"Please enter a {input_list[counter]}: ")
        counter += 1

for i in range(num_words):
    string = string.replace("WORD", word_dict[i+1], 1)

print('\n', string)