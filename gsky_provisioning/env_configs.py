import os
import socket

class Environment:
  def __init__(self, bin_prefix='gsky', **kargs):
    bin_prefix = os.path.abspath(bin_prefix)

    if 'pg_data_prefix' not in kargs:
      if 'PBS_JOBFS' in os.environ:
        pg_data_prefix = os.environ['PBS_JOBFS']
      else:
        pg_data_prefix = 'pg_data'
    else:
        pg_data_prefix = kargs['pg_data_prefix']

    if 'gsky_data_prefix' not in kargs:
      gsky_data_prefix = os.path.join(bin_prefix, 'share/gsky')
    else:
      gsky_data_prefix = kargs['gsky_data_prefix']

    if 'gsky_conf_prefix' not in kargs:
      gsky_conf_prefix = os.path.join(bin_prefix, 'etc/gsky')
    else:
      gsky_conf_prefix = kargs['gsky_conf_prefix']

    ld_lib_path = os.path.join(bin_prefix, 'lib')
    if 'LD_LIBRARY_PATH' in os.environ:
      ld_lib_path = '%s:%s' % (ld_lib_path, os.environ['LD_LIBRARY_PATH'])

    n_cpus = len(os.sched_getaffinity(0))
    if 'GSKY_GRPC_POOL_SIZE' not in kargs:
      grpc_pool_size = n_cpus
    else:
      grpc_pool_size = kargs['GSKY_GRPC_POOL_SIZE']
      if int(grpc_pool_size) <= 0:
        grpc_pool_size = n_cpus

    self.envs = {
      'PKG_CONFIG_PATH': os.path.join(bin_prefix, 'lib/pkgconfig'),
      'PATH': '%s:%s:%s:%s' % (os.path.join(bin_prefix, 'bin'), 
          os.path.join(bin_prefix, 'share/gsky'), 
          os.path.join(bin_prefix, 'share/mas'), 
          os.environ['PATH']),
      'LD_LIBRARY_PATH': ld_lib_path,

      'GOROOT': os.path.join(bin_prefix, 'go'),
      'GOPATH': os.path.join(bin_prefix, 'gopath'),

      'PGUSER': 'postgres',
      'PGDATA': os.path.join(pg_data_prefix, 'data'),
      'PGPORT': '9515',
      'PGHOST': os.path.join(pg_data_prefix, 'socket'),
      'PGDATABASE': 'mas',
      'PG_START_OPTIONS': "-o -h ' ' -k $PGHOST -c max_worker_processes=12 -c shared_buffers=40960 -c temp_buffers=40960 -c work_mem=40960",
      'TMPDIR': os.path.join(pg_data_prefix, 'tmp'),

      'GSKY_DATA_DIR': gsky_data_prefix,
      'GSKY_CONF_DIR': gsky_conf_prefix,
      'GSKY_SHARE_DIR': os.path.join(bin_prefix, 'share/gsky'),
      'GSKY_MAS_SHARE_DIR': os.path.join(bin_prefix, 'share/mas'),
      'GSKY_MASAPI_PORT': '9512',
      'GSKY_GRPC_PORT': '9513',
      'GSKY_GRPC_POOL_SIZE': str(grpc_pool_size),
      'GSKY_OWS_PORT': '9511',
      'GSKY_OWS_HOSTNAME': "http://%s:9511" % socket.gethostname(),
      'GSKY_OWS_STARTUP_TIMEOUT': '180',
    }
