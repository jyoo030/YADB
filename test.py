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

string = str(text_chunk.text).strip()

def countWord(word):

    numWord = 0
    for i in range(1, len(word)-1):
        if word[i-1:i+3] == 'WORD':
            numWord += 1
    return numWord

num_words = countWord(string.strip())

word_id_list = []
for i in range(1, num_words+1):
    user_inputs.find(id=f"w{i}")

word_list = ['a', 'a', 'a', 'a', 'a', 'a']

for word in word_list:
    string = string.replace("WORD", word, 1)

input_list = []
for word in inputs:
    input_list.append(word.text)

print(string)
print(input_list)