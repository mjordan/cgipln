#!/usr/bin/python

"""
Script to generate tab-separated-value file of all documents and their
URLs from the XML files supplied to the CGI-PLN members by the DSP.

Usage:

Update the 'input_directory' setting in config.cfg, and then run the script
as follows:

python generate_tsv.py formats
  -Generates a list of all the document formats recorded in the DSP metadata.
  This list should be generated for each new batch and the 'wanted_formats'
  setting in config.cfg adjusted before running generating the TSV list as below.

python generate_tsv.py tsv
  -Generates a tab-separated list of all the URLs in the DSP metadata, one line
  per URL per document (i.e., if a document is available in more than one format,
  each URL gets its own line).

To save output to a file, use a simple shell redirect, e.g. python generate_tsv.py tsv > out.txt
"""

import sys
# To allow shell redirection to print utf-8 characters.
reload(sys)
sys.setdefaultencoding('UTF8')

import os
import glob
import re
import ConfigParser
import xml.etree.ElementTree as et

config = ConfigParser.ConfigParser()
config.read('config.cfg')
dsp_catalogue_files = glob.glob(os.path.join(config.get('variables', 'input_directory'), '*.xml'))
wanted_formats = config.get('variables', 'wanted_formats').split(',')

dsp_cat_nums = []
num_urls_with_formats = {}

if len(sys.argv) == 2 and sys.argv[1] == 'formats':
    print "Generating URL format report..."

# Loop through each file, pick out all the 'publication' elements, and count the
# values in each 'url' element's 'format' attribute.
for dsp_catalogue_file in dsp_catalogue_files:
    tree = et.parse(dsp_catalogue_file)
    root = tree.getroot()
    publications = root.findall('publication')
    for publication in publications:
        # Get gocCatalogueNumber. Every publication will have one.
        gocCatalogueNumber = publication.find('gocCatalogueNumber').text
        # Check to see if we've seen this publication already. If we have,
        # skip it and move on to the next.
        if gocCatalogueNumber in dsp_cat_nums:
            continue
        else:
            # Remember each publications catalgue number so we can dedupe them.
            dsp_cat_nums.append(gocCatalogueNumber)
            # Get department for each publication. 
            lead_departments = publication.findall('leadDepartment')
            for department in lead_departments:
                department_string = lead_departments[0].text.encode('utf-8')

            # Get URLs for each publication. 
            urls = publication.findall('url')
            for url in urls:
                # Get the value of the 'format' attribute.
                format = url.get('format')

                if len(sys.argv) == 2 and sys.argv[1] == 'formats':
                    # Accumulate the number of occurances of each URL format.
                    if format not in num_urls_with_formats:
                        num_urls_with_formats[format] = 1 
                    else:
                        num_urls_with_formats[format] += 1

                if len(sys.argv) == 2 and sys.argv[1] == 'tsv':
                    if format in wanted_formats:
                        # Titles. Some publication have this:
                        # <title name="Title" lang="eng">Fusarium head blight in Canada</title>
                        titles = publication.findall('title')
                        seriesTitles = publication.findall('seriesTitle')
                        if len(titles):
                            for title in titles:
                                # Caveat: If there are multiple English titles, this code grabs the last one.
                                # Shouldn't be a big deal in this case.
                                title_string = titles[0].text.encode('utf-8')
                        elif len(seriesTitles):
                            # and others have:
                            # <seriesTitle name="Series title" lang="eng">Branching out from the Canadian ... e</seriesTitle>
                            for seriesTitle in seriesTitles:
                                # Caveat: If there are multiple English series titles, this code grabs the last one.
                                # Shouldn't be a big deal in this case.
                                title_string = seriesTitles[0].text.encode('utf-8')
                        else:
                           title_string = 'No title found'

                        # Get the value of the 'generalNote' element so we can add it to the 'Description' field
                        # in the import metadata.
                        generalNotes = publication.findall('generalNote')
                        if len(generalNotes):
                                general_notes_values = [note.text.encode('utf-8') for note in generalNotes]
                                description_string = ' '.join(general_notes_values)
                        

                        # This is the original output
                        # print gocCatalogueNumber + "\t" + department_string + "\t" + title_string + "\t" + url.text
                        # This is the output with metadata
                        print url.text + "\t" + title_string + "\t" + description_string + "\t" + department_string

if len(sys.argv) == 2 and sys.argv[1] == 'formats':
    print "Number of URLs, by format", num_urls_with_formats
