"""arxiv.

Usage:
  scholia.arxiv get-metadata <arxiv>
  scholia.arxiv get-quickstatements [options] <arxiv>

Options:
  -o --output=file  Output filename, default output to stdout

References
----------
  https://arxiv.org

"""

from __future__ import absolute_import, division, print_function

import json

import os
from os import write

import re

import requests

from feedparser import parse as parse_api


USER_AGENT = 'Scholia'

ARXIV_URL = 'https://export.arxiv.org/'


def get_metadata(arxiv):
    """Get metadata about an arxiv publication from website.

    Scrapes the arXiv webpage corresponding to the paper with the `arxiv`
    identifier and return the metadata for the paper in a dictionary.

    Parameters
    ----------
    arxiv : str
        ArXiv identifier.

    Returns
    -------
    metadata : dict
        Dictionary with metadata.

    Notes
    -----
    This function queries arXiv. It must not be used to crawl arXiv.
    It does not look at robots.txt.

    This function currently uses 'abs' HTML pages and not the arXiv API or
    https://arxiv.org/help/oa/index which is the approved way.

    References
    ----------
    - https://arxiv.org
    - https://arxiv.org/help/robots

    Examples
    --------
    >>> metadata = get_metadata('1503.00759')
    >>> metadata['doi'] == '10.1109/JPROC.2015.2483592'
    True

    """
    arxiv = arxiv.strip()

    url = ARXIV_URL + "api/query?id_list=" + arxiv
    response = requests.get(url)

    feed = parse_api(response.content)
    entry = feed.entries[0]

    metadata = {
        'arxiv': arxiv,
        'authornames': [author.name for author in entry.authors],
        'full_text_url': 'https://arxiv.org/pdf/' + arxiv + '.pdf',
        'publication_date': entry.published[:10],

        # Some titles may have a newline in them. This should be converted to
        # an ordinary space character
        'title': re.sub(r'\s+', ' ', entry.title),

        'arxiv_classifications': [tag.term for tag in entry.tags],
    }

    # Optional DOI
    if "arxiv_doi" in entry:
        metadata['doi'] = entry.arxiv_doi

    return metadata


def metadata_to_quickstatements(metadata):
    """Convert metadata to quickstatements.

    Convert metadata about a ArXiv article represented in a dict to a
    format so it can copy and pasted into Magnus Manske quickstatement web tool
    to populate Wikidata.

    This function does not check whether the item already exists.

    Parameters
    ----------
    metadata : dict
        Dictionary with metadata.

    Returns
    -------
    quickstatements : str
        String with quickstatements.

    References
    ----------
    - https://wikidata-todo.toolforge.org/quick_statements.php

    """
    qs = u"CREATE\n"
    qs += u'LAST\tP818\t"{}"\n'.format(metadata['arxiv'])
    qs += u'LAST\tP31\tQ13442814\n'
    qs += u'LAST\tLen\t"{}"\n'.format(metadata['title'].replace('"', '\"'))
    qs += u'LAST\tP1476\ten:"{}"\n'.format(
        metadata['title'].replace('"', '\"'))
    qs += u'LAST\tP577\t+{}T00:00:00Z/11\n'.format(
        metadata['publication_date'][:10])
    qs += u'LAST\tP953\t"{}"\n'.format(
        metadata['full_text_url'].replace('"', '\"'))

    # Optional DOI
    if 'doi' in metadata:
        qs += u'LAST\tP356\t"{}"\n'.format(
            metadata['doi'].replace('"', '\"'))

    # DOI based on arXiv identifier
    qs += u'LAST\tP356\t"10.48550/ARXIV.{}"\n'.format(
            metadata['arxiv'])

    # arXiv classifications such as "cs.LG"
    for classification in metadata['arxiv_classifications']:
        qs += u'LAST\tP820\t"{}"\n'.format(
            classification.replace('"', '\"'))

    for n, authorname in enumerate(metadata['authornames'], start=1):
        qs += u'LAST\tP2093\t"{}"\tP1545\t"{}"\n'.format(
            authorname.replace('"', '\"'), n)
    return qs


def string_to_arxiv(string):
    """Extract arxiv id from string.

    The arXiv identifier part of `string` will be extracted, where the
    identifier pattern should be in the format of a series of digits
    followed by a period followed by a series of digits. Other formats
    will not be matched. If multiple identifier patterns are in the input
    string then only the first is returned.

    Parameters
    ----------
    string : str
        String with arxiv ID.

    Returns
    -------
    arxiv : str or None
        String with arxiv ID.

    Examples
    --------
    >>> string = "http://arxiv.org/abs/1103.2903"
    >>> arxiv = string_to_arxiv(string)
    >>> arxiv == '1103.2903'
    True

    """
    PATTERN = re.compile(r'\d+\.\d+', flags=re.DOTALL | re.UNICODE)
    arxivs = PATTERN.findall(string)
    if len(arxivs) > 0:
        return arxivs[0]
    return None


def main():
    """Handle command-line interface."""
    from docopt import docopt

    arguments = docopt(__doc__)

    if arguments['--output']:
        output_filename = arguments['--output']
        output_file = os.open(output_filename, os.O_RDWR | os.O_CREAT)
    else:
        # stdout
        output_file = 1

    output_encoding = 'utf-8'

    if arguments['get-metadata']:
        arxiv = arguments['<arxiv>']
        metadata = get_metadata(arxiv)
        print(json.dumps(metadata))

    elif arguments['get-quickstatements']:
        arxiv = arguments['<arxiv>']
        metadata = get_metadata(arxiv)
        quickstatements = metadata_to_quickstatements(metadata)
        write(output_file, quickstatements.encode(output_encoding))

    else:
        assert False


if __name__ == '__main__':
    main()
