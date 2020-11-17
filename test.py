from requests_html import HTMLSession
from bs4 import BeautifulSoup

url = r"https://www.madtakes.com/libs/188.html"
session = HTMLSession()
res = session.get(url)
soup = BeautifulSoup(res.content, 'html.parser')

title = res.html.find('title', first=True).text

user_inputs = soup.find(id='mG_188')
text_chunk = soup.find(bgcolor='#d0d0d0')

inputs = user_inputs.find_all('td', align='right')

testing = user_inputs.find_all('input')

string = str(text_chunk.text).strip()

input_list = []
for word in inputs:
    input_list.append(word.text)

id_list = []

def countWord(word):

    numWord = 0
    for i in range(1, len(word)-1):
        if word[i-1:i+3] == 'WORD':
            numWord += 1
    return numWord
    
num_words = countWord(string.strip())

for i in range(1, num_words+1):
    thing = str(user_inputs.find(id=f"w{i}"))
    if 'hidden' in thing:
        index = thing.find('value')
        id_num = thing[index+9]
    else:
        index = thing.find('id')
        id_num = thing[index+5]
    id_list.append(id_num)
print(id_list)
word_dict = {}

word_list = ['a', 'a', 'a', 'a', 'a', 'a']
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

break_text = text_chunk.find('br')
print(break_text.get_text)





print(string)
print(input_list)

