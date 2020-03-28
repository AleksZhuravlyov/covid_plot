#!/usr/bin/env python3
# coding: utf-8

import sys
from flask import Flask,url_for,request,send_from_directory
from covid_web import *

covid_app = Flask(__name__, static_folder='data')

@covid_app.route('/data/<path:query>')
def sendfile(query):
    print('Yes we are', file=sys.stderr)
    return send_from_directory('data/', query)

covid_app.register_blueprint(covid_service)

def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)

covid_app.jinja_env.globals['url_for_other_page'] = url_for_other_page

if __name__ == "__main__":
    covid_app.run()