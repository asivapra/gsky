import argparse
import os
import requests
import socket
import time
import env_configs as cfg
from mas import MAS
from ows import OWS
from worker import Worker
from gsky_config import GSKYConfig

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
  GSKY_GRPC_POOL_SIZE=2,
)

# test crawl file to be ingested into mas
#crawl_files = ['/g/data/cm85/export/published/gsky-prod/wx7-aster.gz',]
crawl_files = ['/short/z00/avs900/aster_crawls/aster-gdal-gsky-1.2.2.tsv.gz',] # Same file as above. Working

# test wms url
url = '%s/ows?time=2012-06-01T00:A00:A00.000Z&srs=EPSG:3857&service=WMS&version=1.1.1&request=GetMap&layers=False_Colour&bbox=13149614.84995544,-3443946.7464169003,13462700.917811524,-3130860.6785608195&width=256&height=256' % envs.envs['GSKY_OWS_HOSTNAME']

######################################################################################
# The above code sets up the basic environment for testing purposes.
# The test data including postgres data files and gsky config.json will be
#   written to test_data under current directory.
#
# The following code performs provisioning by bringing up mas, ows and workers.
######################################################################################

parser = argparse.ArgumentParser()
parser.add_argument('--job_dir', default='~/gsky_dist_jobs')
parser.add_argument('--services', default='ows,mas,worker')
parser.add_argument('--n_workers', type=int, default=1)
args = parser.parse_args()

job_dir = os.path.abspath(os.path.expanduser(args.job_dir))
if not os.path.exists(job_dir):
  raise Exception('%s does not exist or is not accessible' % job_dir)

services = [srv.strip() for srv in args.services.split(',') if len(srv.strip()) > 0]
valid_services = ['ows', 'mas', 'worker']
for srv in services:
  if srv not in valid_services:
    raise Exception('invalid services: %s' % str(services))

hostname = socket.gethostname()

shutdown_file = os.path.join(job_dir, 'shutdown')
worker_file = os.path.join(job_dir, 'worker_%s' % hostname)
mas_file = os.path.join(job_dir, 'mas_%s' % hostname)

try:
  if 'worker' in services:
    worker = Worker(envs=envs.envs)
    worker.start()
    open(worker_file, 'w').close()
    
  if 'mas' in services:
    mas = MAS(envs=envs.envs, mode='r')
    mas.start()
    mas.ingest_data(crawl_files)
    open(mas_file, 'w').close()

  if 'ows' in services:
    ows = OWS(envs=envs.envs)

    mas_port = envs.envs['GSKY_MASAPI_PORT']
    worker_port = envs.envs['GSKY_GRPC_PORT']

    server_conf={
      'service_config':{
        'ows_hostname': '',
        'mas_address': '',
        'worker_nodes': [],
      },
    }

    while True:
      files = [f for f in os.listdir(job_dir) if os.path.isfile(os.path.join(job_dir, f))]
      for f in files:
        if f.startswith('mas_'):
          mas_host = f[len('mas_'):]
          mas_hostname = '%s:%s' % (mas_host, mas_port)
          server_conf['service_config']['mas_address'] = mas_hostname
        if f.startswith('worker_'):
          worker_host = f[len('worker_'):]
          worker_hostname = '%s:%s' % (worker_host, worker_port)
          if worker_hostname not in server_conf['service_config']['worker_nodes']:
            server_conf['service_config']['worker_nodes'].append(worker_hostname)

      if len(server_conf['service_config']['worker_nodes']) >= args.n_workers:
        break

      time.sleep(3)

    conf = GSKYConfig(init_conf=server_conf, envs=envs.envs)

    conf_json = conf.get_config_json(conf_file=os.path.join(curr_path, 'assets/gsky_layers/aster.yaml'))
    with open(os.path.join(gsky_conf_dir, 'config.json'), 'w') as f:
      f.write(conf_json)

    ows.start()

    t0 = time.time()
    res = requests.get(url)
    t = time.time() - t0
    if res.status_code == 200:
      with open('test_wms.png', 'wb') as f:
        f.write(res.content)
      print('%s -> test_wms.png (%.3f secs)' % (url, t))
    else:
      raise Exception(res.text)

  if 'ows' not in services and ('worker' in services or 'mas' in services):
    while True:
      if os.path.exists(shutdown_file):
        break
      time.sleep(3)

finally:
  if 'ows' in services:
    ows.stop()
    open(shutdown_file, 'w').close()

  if 'mas' in services:
    mas.stop()

  if 'worker' in services:
    worker.stop()
