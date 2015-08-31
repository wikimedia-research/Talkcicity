
import urllib2
import json
import string
import codecs
import time
import random
import argparse
import codecs
from xml.sax.saxutils import unescape

parser = argparse.ArgumentParser(description='Extract talk pages associated to one or more Wikipedia articles through the API')
parser.add_argument('-l', action="store", dest="article_list", default="../article_ids_titles.csv", 
                    help="""
                    A file containing the list of articles to be scraped through Wikipedia API (one article title per line, with id and title separated by tab)
                    """)
parser.add_argument('-o', action="store", dest="output_folder", default="./data/talk_pages/", 
                    help="""
                    Output folder for storing the talk pages (one file per article)
                    """)

args = parser.parse_args()

log_folder = './logs/'

#query = 'http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles=%s' #for json
query_xml = u'http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=xml&titles=%s'
xml_template = u'\t<talkpage id="%s" title="%s">\n%s\n\t</talkpage>\n'

import re
archive_MiszaBot_template_re = re.compile(r'\{\{User:MiszaBot/config.*?counter\s+=\s+(\d+)\n.*?\|archive\s+=\s+(.*?)\n', re.DOTALL) #for xml
archive_box_template_re = re.compile(r'\{\{archive.*?\|.*?(\[\[/.*?)\}\}', re.DOTALL) #for xml
link_re = re.compile(r'\[\[([^|]*?)(?:\|.*?)*?\]\]')

# These two should be parsed with an xml parser, not with these regexes.
xml_metadata_re = re.compile(u'<page .* pageid="(.+?)" ns="1" title="(.+?)">', re.DOTALL)
xml_text_re = re.compile('<rev .*? xml:space="preserve">(.*)</rev>', re.DOTALL)

redirectP = re.compile(r'#REDIRECT \[\[(.*)\]\]')

sleep_time = 0

verbose = True
debug = True
debug_more = True

write_log = True
write_error_log = True

if write_log:
    log = codecs.open(log_folder + 'wikitalk_scraper.log', 'w', 'utf-8')
if write_error_log:
    error_log = codecs.open(log_folder + 'wikitalk_scraper_error.log', 'w', 'utf-8')

not_found = []


def get_wikitext_xml(page_title):
#    page_title = page_title.replace(" ", "_")

    if sleep_time > 0:
        time.sleep(sleep_time + sleep_time * (random.random()))

    if debug_more: print u'opening query xml: ' + query_xml % page_title

    try:
        opener = urllib2.build_opener()
        infile = opener.open(query_xml % urllib2.quote(page_title.encode('utf-8')))
        page = infile.read().decode('utf-8')
    except IOError, e:
        if hasattr(e, 'reason'):
            print u'We failed to reach a server. ' + query_xml % page_title
            print u'Reason: ', e.reason
        elif hasattr(e, 'code'):
            print u'The server couldn\'t fulfill the request: ' + query_xml % page_title
            print u'Error code: ', e.code
        if write_error_log:
            try:
                error_log.write(page_title + u'\t' + u'Error opening url ' + query_xml % page_title + u'\n')
            except:
                pass
            error_log.flush()
        return -1, u'', u''

    # TODO: Use an xml parser here, not regex.
    found = re.search(xml_metadata_re, page)
    if found:
        id = found.group(1)
        title = unescape(found.group(2), {"&apos;": "'", "&quot;": '"', "&amp;": "&", "&#039;": "'"})

        if debug_more: print id + u' -> ' + title

        # TODO: Use an xml parser here, not regex.
        found = re.search(xml_text_re, page)
        if found:
            text = found.group(1)

            if debug_more: print u'found text: ' + text[0:30] + u' ...'

            redirect_match = redirectP.match(text)
            if redirect_match:
                redirected_title = unescape(redirect_match.group(1), {"&apos;": "'", "&quot;": '"', "&amp;": "&", "&#039;": "'"})
                if debug: print u'  Found redirect: ' + text
                if write_log: log.write(u'\n  Found redirect: ' + text)
                return  0, redirected_title, text

            else:
                if debug_more: print u'returning %s, %s, %s' % (str(id), title, text[0:20] + ' ...')
                return id, title, text

    if debug_more: print 'returning -1'
    return -1, u'', u''


def wiki_discussion_scraper(article_title):

    if debug_more: print u'wiki_discussion_scraper: calling get_wikitext_xml(%s)' % article_title
    id, title, wiki_text = get_wikitext_xml(article_title)

    #function 'get_wikitext_xml' returns id=0 in case of redirect
    while id == 0:
        if debug: print u'    Following redirect: ' + article_title + u' -> ' + title
        if write_log: log.write(u'\n    Following redirect: ' + article_title + u' -> ' + title)
        temp_title = title
        id, title, wiki_text = get_wikitext_xml(temp_title)
        if id == 0 and title == temp_title:
            print u'something wrong with redirects: ' + title
            break

    if id <= 0:
        return u''

    xml = u'<article id="%s" title=%s>\n' % (id, title)

    last_xml = xml_template % (id, title, wiki_text)

    # only the current (not archived) talk page
    counter = 0
    archive_pages = []

    found = re.search(archive_box_template_re, wiki_text)
    if found:
        archives_box = re.findall(link_re, found.group(1))
        if debug: print u'\tarchive box found: ' + unicode(archives_box)
        if write_log: log.write(u'\n\tarchive box found: ' + unicode(archives_box))
        for a in archives_box:
            archive_pages.append(title + a)

    # TODO: Check this for Unicode pages
    archive_links_re = re.compile(r'\[\[(' + title + '/[^|^#]*?)(?:\|.*?)?\]\]')
    found = re.findall(archive_links_re, wiki_text)
    if found:
        if debug: print '\tarchive links found: ' + str(found)
        if write_log: log.write('\n\tarchive links found: ' + str(found) )
        archive_pages += found

    found = re.search(archive_MiszaBot_template_re, wiki_text)
    if found:
        counter, archive = found.group(1), found.group(2)
        for i in range(1, int(counter) + 1):
            archive_pages.append(archive.replace("%(counter)d", str(i)))
        if debug: print u'\tMisznaBot archives found: ' + unicode(counter) + u' -> ' + archive #str(archive_pages)
        if write_log: log.write(u'\n\tMisznaBot archives found: ' + unicode(counter) + u' -> ' + archive) #str(archive_pages)

    archive_pattern = u'%s/Archive_' % title
    last_i = 0
    i = 1
    while i > last_i:
        last_i = i
        id, title, wiki_text = get_wikitext_xml(archive_pattern + str(i))
        if id > 0:
            if archive_pattern + unicode(i) not in archive_pages and archive_pattern.replace('_', ' ') + unicode(i) not in archive_pages:
                archive_pages.append(archive_pattern + str(i))
            else:
                if debug_more: print u'\tSkipped repeated archive page: ' + archive_pattern + unicode(i)
                if write_log: log.write(u'\n\tSkipped repeated archive page: ' + archive_pattern + unicode(i) )

            i += 1

    if i > 1:
        if debug: print u'\tLooking for "Archive_<n>" pattern, found ' + unicode(i-1) + u' archives, until: ' + archive_pattern + unicode(i-1)
        if write_log: log.write(u'\n\tLooking for "Archive_<n>" pattern, found ' + unicode(i-1) + u' archives, until: ' + archive_pattern + unicode(i-1) )
    else:
        if write_log: log.write('\n\t\tNot found: ' + archive_pattern + str(i) )

    n_archives_written = 0
    processed_archives = []
    for a in archive_pages:
        if a not in processed_archives and string.replace(a, '_', ' ') not in processed_archives:
            id, title, wiki_text = get_wikitext_xml(a)
            if id > 0:
                xml += xml_template % (id, title, wiki_text)
                n_archives_written += 1
            else:
                if debug: print u'     Could not access archive %s' % a
                if write_log: log.write(u'\n     Could not access archive %s' % a )
                if write_error_log:
                    error_log.write(a + u'\t' + u'Could not access archive %s\n' % a )
                    error_log.flush()
        processed_archives.append(a)
        processed_archives.append(string.replace(a, '_', ' '))

    if verbose or debug: print u"   %s: written current talk page and %d archive pages" %(article_title, n_archives_written)
    xml +=  last_xml
    xml += u"</article>"

    return xml

# Identify the namespace to prepend to the page title.
def namespace_select(namespace):
    # if desired this could be pulled out somehow for an API check of what namespaces it actually has but that's gravy
    namespace_titles = {1: u"Talk:", 3: u"User talk:", 4: u"Wikipedia:", 5: u"Wikipedia talk:"}
    return namespace_titles[namespace];

def load_id_list_from_file(file_name):
  article_identifiers = []  # should be a list of tuples with (title, namespace number)
  with codecs.open(file_name, 'r', 'utf-8') as f:
      for line in f:
          info_list = line.strip().split('\t')  # strip newline, split on tab
          article_identifiers.append((info_list[0].strip(), info_list[1].strip(), info_list[2].strip()))
  return article_identifiers;

if __name__ == '__main__':
    entries = load_id_list_from_file(args.article_list)
    for entry in entries:
      if verbose or debug: print u'\nProcessing article: ' + unicode(entry[1]) + u' ' + entry[2]
      if write_log:
          try:
              log.write(u'\n\n' + unicode(entry[1]) + u' ' + unicode(entry[2]) )
          except:
              log.write(u'\n\n' + unicode(entry[1]) + u' Exception writing article title')
      t = string.replace(entry[2],u' ', u'_')
      full_title = namespace_select(entry[0]) + entry[2]
      xml = wiki_discussion_scraper(full_title)
      print(full_title)
      if xml == '':
          not_found.append(entry[2])
          if debug: print u'   Talk page not found: ' + full_title
          if write_log:
              try:
                  log.write(u'\n   Talk page not found: ' + full_title)
              except:
                  log.write(u'\n   Talk page not found: ' + entry[1] + u' Exception writing article title')
      else:
          f_out = codecs.open(args.output_folder + 'article_talk_' + str(entry[1]) + '.wikitext', 'w', 'utf-8')
          f_out.write(xml)
          f_out.close()
      log.flush()

    print '\nEnd. Not found: %d articles:' % len(not_found)
    for t in not_found: print u'  ' + t
