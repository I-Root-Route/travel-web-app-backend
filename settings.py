import configparser

conf = configparser.ConfigParser()
conf.read('settings.ini')

elastic_url = conf['database']['elastic_url']
elastic_user = conf['database']['elastic_user']
elastic_pass = conf['database']['elastic_pass']
users_index = conf['database']['users_index']

countries = eval((conf['app_data']['countries']))
valid_currencies = eval(conf['app_data']['valid_currencies'])

colors = eval(conf['colors_for_calendar_vue']['colors'])

