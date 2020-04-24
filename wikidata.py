#!/usr/bin/env python
# coding: utf-8

from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions
import sys
import json
import time


def getpopulation(query, sparql):
    sparql.setQuery("""
    SELECT DISTINCT ?item ?itemLabel ?population
    WHERE {
      ?item rdfs:label "%s"@en.
      ?item wdt:P31 wd:Q3624078.
      ?item wdt:P1082 ?population.
      ?item rdfs:label ?itemLabel.
      FILTER (lang(?itemLabel) = "ru")
           }
      LIMIT 1
        """ % query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
    except SPARQLExceptions.QueryBadFormed:
        return None
    if len(results["results"]["bindings"]) > 0:
        bindings = results["results"]["bindings"][0]
        cur_population = bindings['population']["value"].strip()
        cur_rus_name = bindings['itemLabel']["value"].strip()
        return cur_population, cur_rus_name
    else:
        return None, None


countries_file = sys.argv[1]

sparqlpoint = SPARQLWrapper("https://query.wikidata.org/sparql",
                            agent="SPARQLWrapper bot/1.8.5 "
                                  "(https://dev.rus-ltc.org/covid/;covidbot@example.org)")


with open(countries_file, 'r') as f:
    countries = json.load(f)

countries2 = {}

for country in countries:
    time.sleep(2)
    print('Processing', country, file=sys.stderr)
    countries2[country] = {'population': None, 'rus': None}
    population, rus_name = getpopulation(country, sparqlpoint)
    if population and rus_name:
        countries2[country]['population'] = int(population)
        countries2[country]['rus'] = rus_name
    else:
        print('There was an error!', file=sys.stderr)

out = json.dumps(countries2, ensure_ascii=False, indent=4)

print(out)
