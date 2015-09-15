#!/usr/bin/python

import getopt
import os
import re
import sys
import version

import occi
import render


inputmime = 'text/plain'
outputmime = 'text/plain'
messagetype = 'categories'

messagetypes = ['categories', 'entities', 'resource']


def usage(name=__file__):
    print '%s [OPTIONS]\n\
\n\
OPTIONS:\n\
  -h, --help\n\
  -i, --input-mime MIME-TYPE .... input mime-type [text/plain]\n\
  -o, --output-mime MIME-TYPE ... output mime-type [text/plain]\n\
  -t, --type OCCI-TYPE .......... OCCI message type [categories]\n\
  -V, --version ................. print version information\n\
\n\
MIME-TYPE: text/plain, text/occi, text/uri-list\n\
OCCI-TYPE: %s\n\
' % (os.path.basename(name), ', '.join(messagetypes))


def read_input(strip=False):
    for line in sys.stdin:
        if strip:
            yield line.rstrip('\n\r')
        else:
            yield line


def main(argv=sys.argv[1:]):
    global inputmime, outputmime, messagetype

    occi_parser = None
    occi_renderer = None

    try:
        opts, args = getopt.getopt(argv, 'hi:o:t:V', ['--help', '--input-mime=', '--output-mime=', 'type=', 'version'])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ['-h', '--help']:
            usage()
            sys.exit()
        elif opt in ['-i', '--input-mime']:
            inputmime = arg
        elif opt in ['-o', '--output-mime']:
            outputmime = arg
        elif opt in ['-t', '--type']:
            messagetype = arg
        elif opt in ["-V", "--version"]:
            print version.__version__
            sys.exit()

    if messagetype not in messagetypes:
        print >> sys.stderr, 'OCCI message type expected: %s' % ', '.join(messagetypes)
        sys.exit(2)

    occi_parser = render.create_renderer(inputmime)
    if not occi_parser:
        print >> sys.stderr, 'OCCI parser can\'t be initialized (wrong mime-type "%s"?)' % inputmime
        sys.exit(2)

    occi_renderer = render.create_renderer(outputmime)
    if not occi_renderer:
        print >> sys.stderr, 'OCCI renderer can\'t be initialized (wrong mime-type "%s"?)' % outputmime
        sys.exit(2)

    if re.match(r'text/occi(;.*)?$', inputmime):
        body = None
        headers = list(read_input(strip=False))
    else:
        body = list(read_input(strip=True))
        headers = None

    try:
        if messagetype in ['categories']:
            categories = occi_parser.parse_categories(body, headers)
            [body, headers] = occi_renderer.render_categories(categories)
        elif messagetype in ['entities']:
            urls = occi_parser.parse_locations(body, headers)
            [body, headers] = occi_renderer.render_locations(urls)
        elif messagetype in ['resource']:
            [categories, links, attributes] = occi_parser.parse_resource(body, headers)
            [body, headers] = occi_renderer.render_resource(categories, links, attributes)
    except occi.ParseError as perr:
        print >> sys.stderr, str(perr)
        sys.exit(1)
    except occi.RenderError as rerr:
        print >> sys.stderr, str(rerr)
        sys.exit(1)

    if body:
        sys.stdout.write(body)
    if headers:
        sys.stdout.write('\n'.join(headers) + '\n')

if __name__ == '__main__':
    main(sys.argv[1:])
