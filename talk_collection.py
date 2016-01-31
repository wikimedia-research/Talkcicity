# Python 3 please.
from wikichatter import talkpageparser
import re
import mwparserfromhell as mwp
import pickle
import warnings

class talk_collection:
  
  # Write comments out
  def write_comments(self, file):
    with open("parsed_sample.pickle", "wb") as file:
      pickle.dump(self.talk_entries, file)
  
  # Extract sections from the page
  def extract_sections(page_text): # I might rewrite those so that it's more of an "apply FUN to each section"
    for section in page_text['sections']:
      section = extract_comments(section)
    return(page_text)
  
  # Once we've got an individual section, this goes through each comment getting the text
  def extract_comments(section):
    for comment in section['comments']:
      comment['text_blocks'] = parse_text(comment['text_blocks'])
    return(section)
  
  # Get the actual comment text :/
  def parse_text(comment):
    comment = re.sub("\\[\\[(File|Image):.*\\]\\]", "", '\n'.join(comment)) # File and image links go wonky when mwp handles it.
    comment = re.sub("<article id=.*\\n\\t<talkpage.*>", "", comment) # Merge and remove content metadata
    comment = mwp.parse(comment).strip_code(normalize=True, collapse=True)
    comment = re.sub("(<!--.*-->|</article>|</talkpage>)", "", comment)
    return(comment)
  
  # The constructor. Takes in a list of files, parses and cleans the comments and stores
  # the resulting structures in the talk_collection object.
  def __init__(self, files, warn = False):
    
    self.talk_entries = list()
    self.failed_files = list()
    
    for file in files:
      with open(file, "r") as f:
        text = f.read()
      try:
        parsed = talkpageparser.parse(text)
        self.talk_entries.append(extract_sections(parsed))
      except:
        self.failed_files.append(file)
      
    if warn is True:
      if len(self.failed_files) > 0:
        warnings.warn("Some files failed to be read and parsed. See the failed_files list in the talk_collection object")
        
