# Python 3 please.
from wikichatter import talkpageparser
from os import listdir
import random
import re
import mwparserfromhell as mwp

def extract_sections(page_text):
  for section in page_text['sections']:
    section = extract_comments(section)
  return(page_text)

# Once we've got an individual section, this goes through each comment getting the text
def extract_comments(section):
  for comment in section['comments']:
    comment['text_blocks'] = extract_text(comment['text_blocks'])
  return(section)

# Get the actual comment text :/
def extract_text(comment):
  comment = re.sub("\\[\\[(File|Image):.*\\]\\]", "", '\n'.join(comment)) # File and image links go wonky when mwp handles it.
  comment = re.sub("<article id=.*\\n\\t<talkpage.*>", "", comment) # Merge and remove content metadata
  comment = mwp.parse(comment).strip_code(normalize=True, collapse=True)
  comment = re.sub("(<!--.*-->|</article>|</talkpage>)", "", comment)
  return(comment)

# Get the wikitext files, subset
files = random.sample(listdir("./data/talk_pages"), 100)

output = list()
for file in files:
  f_path = "./data/talk_pages/" + file;
  with open(f_path, "r") as f:
    text = f.read()
    try:
      parsed = talkpageparser.parse(text)
      output = (output + extract_sections(parsed))
    except:
      pass

