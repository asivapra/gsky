import subprocess as sp
import sys
import argparse
import os

class PG:
  def __init__(self, 
      pg_config='pg_config',
      pg_data='pg_data',
      pg_db='',
      pg_user='postgres',
      mode='r',
      envs=None):

    self.envs = {}
    if envs is not None:
      for k, v in envs.items():
        self.envs[k] = v

    self.pg_data_base = os.path.abspath(pg_data)
    if 'PGDATA' not in self.envs:
      self.envs['PGDATA'] = os.path.join(self.pg_data_base, 'data')
    self.pg_data_dir = self.envs['PGDATA']

    if 'PGHOST' not in self.envs:
      self.envs['PGHOST'] = os.path.join(self.pg_data_base, 'socket')
    
    self.pg_socket_dir = self.envs['PGHOST']

    if 'PGUSER' not in self.envs:
      self.envs['PGUSER'] = pg_user
    self.pg_user = self.envs['PGUSER']

    if 'PGDATABASE' not in self.envs:
      self.envs['PGDATABASE'] = pg_db
    self.pg_db = self.envs['PGDATABASE']

    if 'TMPDIR' in self.envs:
      self.pg_temp_dir = self.envs['TMPDIR'] 
    else:
      self.pg_temp_dir = '' 

    self.pg_config = pg_config
    self.mode = mode

    self.config_pg_environment()

  def __enter__(self):
    self.start_pg()
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.stop_pg()

  def psql(self, sql, opts=''):
    return self.check_output(
'''psql {opts} <<EOF
{cmd}
EOF'''.format(opts=opts, cmd=sql))

  def check_output(self, cmd):
    outputs = sp.check_output(cmd, env=self.envs, shell=True, universal_newlines=True)
    return(outputs)

  def exec(self, cmd):
    sp.run(cmd, env=self.envs, shell=True, stdout=sys.stdout, stderr=sys.stderr, check=True)

  def config_pg_environment(self):
    pg_configs = sp.check_output(self.pg_config, env=self.envs, shell=True, universal_newlines=True).strip()

    for cfg in pg_configs.split('\n'):
      kv = cfg.split('=') 
      k = kv[0].strip()
      v = kv[1].strip()

      if k.lower() == 'bindir':
        if 'PATH' in os.environ:
          path_env = os.environ['PATH']
        self.envs['PATH'] = '%s:%s' % (v, path_env)
      elif k.lower() == 'libdir':
        self.envs['LD_LIBRARY_PATH'] = '%s' % v
        if 'LD_LIBRARY_PATH' in os.environ:
          ld_env = os.environ['LD_LIBRARY_PATH']
          self.envs['LD_LIBRARY_PATH'] += ':%s' % ld_env

    self.pg_configs = pg_configs

  def init_pg(self):
    if not os.path.exists(self.pg_data_dir):
      os.makedirs(self.pg_data_dir)

    if len(self.pg_temp_dir) > 0:
      if not os.path.exists(self.pg_temp_dir):
        os.makedirs(self.pg_temp_dir)

    sp.run('set -x;initdb -U %s' % self.pg_user, env=self.envs, stdout=sys.stdout, stderr=sys.stderr, shell=True, check=True)
    if not os.path.exists(self.pg_socket_dir):
      os.makedirs(self.pg_socket_dir)

  def stop_pg(self):
    pg_pid = os.path.join(self.pg_data_dir, 'postmaster.pid')
    sp.run('pg_ctl -w -t 10 stop; [ -f "{pid}" ] && kill -9 $(head -n1 "{pid}")'.format(pid=pg_pid), 
      env=self.envs, stdout=sys.stdout, stderr=sys.stderr, shell=True)

  def start_pg(self):
    self.stop_pg()
    if self.mode == 'w':
      sp.run('set -x;rm -rf "%s"' % self.pg_data_dir, env=self.envs, stdout=sys.stdout, stderr=sys.stderr, shell=True)
      self.init_pg()
    elif self.mode == 'r':
      if not os.path.exists(os.path.join(self.pg_data_dir, 'PG_VERSION')):
        self.init_pg()

    sp.run('''set -x;pg_ctl "$PG_START_OPTIONS" -w -t 10 start''', env=self.envs, stdout=sys.stdout, stderr=sys.stderr, shell=True, check=True)

if __name__ == "__main__":
  argparser = argparse.ArgumentParser()
  argparser.add_argument('--pg_config', default='pg_config')
  argparser.add_argument('--pg_data', default='pg_data')
  argparser.add_argument('--pg_db', default='')
  argparser.add_argument('--pg_user', default='postgres')

  args = argparser.parse_args()
  kv_args = {}

  for kv in args._get_kwargs():
    kv_args[kv[0]] = kv[1]

  # tests
  with PG(**kv_args, mode='w') as pg:
    outs = pg.psql('''  select 1;
   select 2; 

    create table if not exists test_tbl as 
    select 'aaa' as col1, 'bbb' as col2, 123 as col3, 456 as col4;
    ''')

    print(outs)

    outs = pg.check_output(''' which git ''')
    print(outs)

  with PG() as pg:
    outs = pg.psql(''' explain (analyze, timing on) select * from test_tbl; ''', '-t')
    print(outs)

