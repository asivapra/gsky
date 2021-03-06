import os
import sys
import requests
import time
import env_configs as cfg
from mas import MAS
from ows import OWS
from worker import Worker
from gsky_config import GSKYConfig
try:
	dataset = sys.argv[1]
except:
	sys.exit('ERROR: Must specify a dataset. e.g. "python3 provision_single_node.py dea". Exitting!')
	
curr_path = os.path.dirname(os.path.realpath(__file__))

gsky_conf_dir = os.path.join(curr_path, 'test_data/gsky_conf')
if not os.path.exists(gsky_conf_dir):
  os.makedirs(gsky_conf_dir)

envs = cfg.Environment(
  # bin_prefix 'gsky' is the default path generated by build_gsky.py
  bin_prefix=os.path.join(curr_path, 'gsky'), 

  # pg_data_prefix is the path for postgres database files.
  pg_data_prefix=os.path.join(curr_path, 'test_data/pg_data'),

  # gsky_conf_prefix is where the GSKY config.json locates.
  gsky_conf_prefix=gsky_conf_dir,

  # Unsetting or setting GSKY_GRPC_POOL_SIZE to non-positive value will be defaulted to number of cores.
  # Here we set it to 2 for testing purpose. 
  GSKY_GRPC_POOL_SIZE=32,
)
conf = GSKYConfig(envs=envs.envs)
crawl_files = ''
url = ''
conf_json = ''
if dataset == 'aster':
#	crawl_files = ['/g/data/cm85/export/published/gsky-prod/wx7-aster.gz',]
	crawl_files = ['/short/z00/avs900/aster_crawls/aster-gdal-gsky-1.2.2.tsv.gz',] # Same file as above. Working
	url = '%s/ows?time=2012-06-01T00:A00:A00.000Z&srs=EPSG:3857&service=WMS&version=1.1.1&request=GetMap&layers=False_Colour&bbox=13149614.84995544,-3443946.7464169003,13462700.917811524,-3130860.6785608195&width=256&height=256' % envs.envs['GSKY_OWS_HOSTNAME']
	conf_json = conf.get_config_json(conf_file=os.path.join(curr_path, 'assets/gsky_layers/aster.yaml'))
	
if dataset == 'dea':
	crawl_files = ['/short/z00/avs900/dea_crawls/landsat8_nbar_avs.gz',]

	url = '%s/ows?time=2019-05-07T00:00:00.000Z&srs=EPSG:3857&transparent=true&format=image/png&exceptions=application/vnd.ogc.se_xml&styles=&tiled=true&feature_count=101&service=WMS&version=1.1.1&request=GetMap&layers=landsat5_nbar_16day&bbox=15341217.324948017,-2974317.644632779,15419488.841912035,-2896046.127668757&width=256&height=256' % envs.envs['GSKY_OWS_HOSTNAME']
#	url = '%s/ows?time=1986-08-15T00:00:00.000Z&srs=EPSG:3857&service=WMS&version=1.1.1&request=GetMap&layers=landsat5_nbar_16day&bbox=15419488.841912035,-3443946.7464169003,15497760.358876053,-3365675.229452882&width=256&height=256' % envs.envs['GSKY_OWS_HOSTNAME'] 
#	url = '%s/ows?time=1986-08-15T00:00:00.000Z&srs=EPSG:3857&service=WMS&version=1.1.1&request=GetMap&layers=landsat5_nbar_16day&bbox=13149614.84995544,-3443946.7464169003,13462700.917811524,-3130860.6785608195&width=256&height=256' % envs.envs['GSKY_OWS_HOSTNAME']
	conf_json = conf.get_config_json(conf_file=os.path.join(curr_path, 'assets/gsky_layers/dea_nbar.yaml'))
	
if dataset == 'geoglam':
	crawl_files = ['/short/z00/avs900/dea_crawls/tc43-modis.gz',]
	url = '%s/ows?time=2001-01-01T00:00:00.000Z&srs=EPSG:3857&service=WMS&version=1.1.1&request=GetMap&layers=modis_fract_cov_8day&bbox=13149614.84995544,-3443946.7464169003,13462700.917811524,-3130860.6785608195&width=256&height=256' % envs.envs['GSKY_OWS_HOSTNAME']
	conf_json = conf.get_config_json(conf_file=os.path.join(curr_path, 'assets/gsky_layers/geoglam.yaml'))

if dataset == 's2':
	crawl_files = ['/short/z00/avs900/dea_crawls/if87-sentinel2_avs_10000.gz',]
	url = '%s/ows?time=2017-10-23T00:00:00.000Z&srs=EPSG:3857&service=WMS&version=1.1.1&request=GetMap&layers=sentinel2_nbart_daily&bbox=14949859.74012791,-2661231.576776698,15028131.257091936,-2582960.059812676&width=256&height=256' % envs.envs['GSKY_OWS_HOSTNAME']
	conf_json = conf.get_config_json(conf_file=os.path.join(curr_path, 'assets/gsky_layers/dea_sentinel.yaml'))

######################################################################################
# The above code sets up the basic environment for testing purposes.
# The test data including postgres data files and gsky config.json will be
#   written to test_data under current directory.
#
# The following code performs provisioning by bringing up mas, ows and a worker.
######################################################################################


#conf_json = conf.get_config_json(conf_file=os.path.join(curr_path, 'assets/gsky_layers/geoglam.yaml'))
#conf_json = conf.get_config_json(conf_file=os.path.join(curr_path, 'assets/gsky_layers/dea.yaml'))
with open(os.path.join(gsky_conf_dir, 'config.json'), 'w') as f:
  f.write(conf_json)
mas = MAS(envs=envs.envs, mode='r')
ows = OWS(envs=envs.envs)
worker = Worker(envs=envs.envs)

try:
  worker.start()
  mas.start()
  mas.ingest_data(crawl_files)

  ows.start()
  print(url)
  t0 = time.time()
  res = requests.get(url)
  t = time.time() - t0
  if res.status_code == 200:
    with open('test_wms.png', 'wb') as f:
      f.write(res.content)
    print('%s -> test_wms.png (%.3f secs)' % (url, t))
  else:
    raise Exception(res.text)

finally:
#  ows.stop()
#  mas.stop()
#  worker.stop()
#  print ("Finished! Shutting down the servers.")  
  print ("Finished! Leaving the servers running.")
