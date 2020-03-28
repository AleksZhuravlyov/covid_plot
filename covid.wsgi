import sys
sys.path.insert(0, '/var/www/html/covid')
from run_covid import covid_app as application
application.debug = True
