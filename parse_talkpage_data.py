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

# Generate versions for each comment too
comments = parsed_versions.get_text()
with open("parsed_sample_text.tsv", "w") as file:
  for comment in comments:
    file.write(comment[0] + "\t" + comment[1] + "\n")

with open("parsed_sample_text.txt", "w") as file:
  for comment in comments:
    file.write(comment[0] + "-----" + comment[1] + "\n")
#     comment = re.sub("\\[\\[(File|Image):.*\\]\\]", "", ' '.join(comment)) # File and image links go wonky when mwp handles it.
#     comment = re.sub("<article id=.*\\n\\t<talkpage.*>", "", comment) # Merge and remove content metadata
#     comment = mwp.parse(comment).strip_code(normalize=True, collapse=True)
