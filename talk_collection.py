# Python 3 please.
from wikichatter import talkpageparser
from wikichatter import signatureutils
import re
import mwparserfromhell as mwp
import pickle
import warnings

class talk_collection:
  
  # Retrieve the comments, with context if desired.
  def get_text(self, context=True):
    output = list()
    for entry in self.talk_entries:
      for section in entry['sections']:
        for i, index in enumerate(section['comments']):
          if i == 0:
            output.append(["N/A", index["text_blocks"]])
          else:
            output.append([section["comments"][i-1]["text_blocks"], index["text_blocks"]])
    return(output)
  
  # Write comments out
  def write_comments(self, file):
    with open("parsed_sample.pickle", "wb") as file:
      pickle.dump(self.talk_entries, file)
  
  # Extract sections from the page
  def extract_sections(self, page_text): # I might rewrite those so that it's more of an "apply FUN to each section"
    for section in page_text['sections']:
      section = self.extract_comments(section)
    return(page_text)
  
  # Once we've got an individual section, this goes through each comment getting the text
  def extract_comments(self, section):
    for comment in section['comments']:
      comment['text_blocks'] = self.parse_text(comment['text_blocks'])
    return(section)
  
  # Get the actual comment text :/
  def parse_text(self, comment):
    comment = re.sub("(\t|\n)", "", ' '.join(comment)) # Smush it together
    
    # Handle signatures!
    if signatureutils.has_signature(comment):
      sig = signatureutils._extract_rightmost_signature(comment)
      if(len(sig)):
        sig = sig["start"]
        if sig is not 0:
          sig-=1
        comment = comment[:sig]
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
          self.talk_entries.append(self.extract_sections(parsed))
        except:
          self.failed_files.append(file)
    if warn is True:
      if len(self.failed_files) > 0:
        warnings.warn("Some files failed to be read and parsed. See the failed_files list in the talk_collection object")
        
