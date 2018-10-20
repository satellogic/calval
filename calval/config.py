import os
import appdirs

lib_dir = os.path.abspath(os.path.dirname(__file__))
data_dir = appdirs.user_data_dir(appname='calval', appauthor='satellogic')
shapes_dir = lib_dir + '/site_data'
scenes_dir = data_dir + '/scenes'
dl_dir = data_dir + '/downloads'
normalized_dir = data_dir
cache_dir = appdirs.user_cache_dir(appname='calval', appauthor='satellogic')
