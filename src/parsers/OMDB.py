import getopt
import json
from multiprocessing.pool import Pool
import re
import urllib2

from rdflib import Graph, Namespace, URIRef, RDF, RDFS, Literal
import sys

import common

__author__ = "prayzzz"

JSON_IN_FILE = "tunefind.json"
JSON_OUT_FILE = "omdb.json"
RDF_OUT_FILE = "omdb.owl"
LOAD_FROM_WEB = False
CONVERT_TO_RDF = False

EP_OMDB = "http://www.omdbapi.com/?t=%s&y=&plot=short&r=json"

BASE_URI = "http://imn.htwk-leipzig.de/pbachman/ontologies/omdb#%s"
NS_OMDB = Namespace("http://imn.htwk-leipzig.de/pbachman/ontologies/omdb#")
NS_DBPEDIA_OWL = Namespace("http://dbpedia.org/ontology/")
NS_DBPPROP = Namespace("http://dbpedia.org/property/")


def convert_to_rdf():
    print ""
    print "Convert to RDF..."

    movies = common.read_json(JSON_OUT_FILE)

    g = Graph()
    g.bind("", NS_OMDB)
    g.bind("dbpedia-owl", NS_DBPEDIA_OWL)
    g.bind("dbpprop", NS_DBPPROP)

    for m in movies:
        movie = URIRef(BASE_URI % common.encodeString(m["title"]))
        g.add((movie, RDF.type, NS_DBPEDIA_OWL.Film))
        g.add((movie, RDFS.label, Literal(m["title"])))
        g.add((movie, NS_DBPPROP.title, Literal(m["title"])))
        g.add((movie, NS_DBPEDIA_OWL.imdbId, Literal(m["imdb_id"])))

    common.write_rdf(RDF_OUT_FILE, g)


def process_movie(m):
    print m["title"]

    re_match = re.search("^(.*?)(\s\(\d{4}\))?$", m["title"])

    if len(re_match.groups()) < 2:
        title = m["title"]
    else:
        title = re_match.group(1)

    title = title.replace(" ", "+")
    url = EP_OMDB % urllib2.quote(title)
    data = json.loads(common.request_url(url))

    movie = {"title": m["title"], "imdb_id": data["imdbID"]}
    return movie


def load_from_web():
    print ""
    print "Loading from Web..."

    movies = common.read_json(JSON_IN_FILE)

    pool = Pool(5)
    results = [pool.apply_async(process_movie, [m]) for m in movies]

    omdb_movies = []
    for w in results:
        w.wait()
        omdb_movies.append(w.get())

    common.write_json(JSON_OUT_FILE, omdb_movies)


def usage():
    print "OMDB.py"
    print ""
    print "Usage:"
    print "python OMDB.py"
    print " -w \t Load data from Web"
    print " -r \t Convert data to RDF"


def main():
    if LOAD_FROM_WEB:
        load_from_web()

    if CONVERT_TO_RDF:
        convert_to_rdf()


if __name__ == "__main__":
    try:
        options = getopt.getopt(sys.argv[1:], "wr", ["web", "rdf"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in options[0]:
        if opt == "-w":
            LOAD_FROM_WEB = True
        elif opt == "-r":
            CONVERT_TO_RDF = True

    main()
