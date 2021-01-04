import configparser

conf = configparser.ConfigParser()
conf.read('settings.ini')

countries = eval((conf['app_data']['countries']))
valid_currencies = eval(conf['app_data']['valid_currencies'])

colors = eval(conf['colors_for_calendar_vue']['colors'])

