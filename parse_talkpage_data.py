# Python 3 please.
from wikichatter import talkpageparser
from os import listdir
import random
import re
import mwparserfromhell as mwp

def extract_sections(page_text):
  output = list()
  for section in page_text['sections']:
    output = output + extract_comments(section)
  return(output)

# Once we've got an individual section, this goes through each comment getting the text
def extract_comments(section):
  output = list()
  for comment in section['comments']:
    output.append(extract_text(comment['text_blocks']))
  return(output)

# Get the actual comment text :/
def extract_text(comment):
  comment = re.sub("\\[\\[(File|Image):.*\\]\\]", "", '\n'.join(comment)) # File and image links go wonky when mwp handles it.
  comment = re.sub("<article id=.*\\n\\t<talkpage.*>", "", comment) # Merge and remove content metadata
  comment = mwp.parse(comment).strip_code(normalize=True, collapse=True)
  comment = re.sub("(<!--.*-->|</article>|</talkpage>)", "", comment)
  return(comment)

# Get the wikitext files, subset
files = random.sample(listdir("./data/talk_pages"), 100)

for file in files:
  f_path = "./data/talk_pages/" + file;
  with open(f_path, "r") as f:
    text = f.read()
    parsed = talkpageparser.parse(text)
