# Python 3 please.
from wikichatter import talkpageparser
from os import listdir
import random

# Get the wikitext files, subset
files = random.sample(listdir("./data/talk_pages"), 100)

for file in files:
    f_path = "./data/talk_pages/" + file;
    with open(f_path, "r") as f:
        text = f.read()
        parsed = talkpageparser.parse(text)
