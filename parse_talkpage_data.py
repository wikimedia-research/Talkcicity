# Python 3 please.
import random
from os import listdir
import talk_collection

# Get the wikitext files, subset
dir = "./data/talk_pages/"
files = [dir + filestring for filestring in random.sample(listdir(dir), 100)]

# Generate parsed versions and write out
parsed_versions = talk_collection.talk_collection(files)
parsed_versions.write_comments("parsed_sample.pickle")
