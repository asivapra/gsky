import subprocess as sp
import os
import signal
import re
from pg_sql import PG
import sys
import env_configs as cfg

class MAS:
  def __init__(self, mode='r', envs=None):
    if envs is None:
      self.envs = cfg.Enviornment().envs
    else:
      self.envs = envs

    self.pg = PG(pg_data=self.envs['PGDATA'], pg_db='mas', mode=mode, envs=self.envs)
    self.is_pg_init = False
    self.is_mas_init = False

  def init_pg(self):
    if not self.is_pg_init:
      self.pg.start_pg()
      try:
        self.pg.psql('''select * from shards limit 1;''')
      except:
        self.pg.exec('''(set -xeu
          cd "$GSKY_MAS_SHARE_DIR" && unset PGDATABASE && psql -f schema.sql && psql -f mas.sql
          )''')
      self.is_pg_init = True

  def start(self):
    self.init_pg()
    if not self.is_mas_init:
      self.mas_proc = sp.Popen('''(set -xeu
        cd "$GSKY_SHARE_DIR" && ./masapi -port $GSKY_MASAPI_PORT -dbhost $PGHOST
        )''', env=self.envs, shell=True, stdout=sys.stdout, stderr=sys.stderr, preexec_fn=os.setpgrp)

      self.is_mas_init = True

  def stop(self):
    if self.is_mas_init:
      os.killpg(os.getpgid(self.mas_proc.pid), signal.SIGKILL)
    self.pg.stop_pg()

  def ingest_data(self, files):
    self.init_pg()
    for i, f in enumerate(files):
      line = self.pg.check_output('''zcat "%s"|head -n1''' % f)
      parts = line.split('\t')
      assert len(parts) == 3, 'invalid gsky tsv file format'

      path_parts = parts[0].split('/')
      prefix_parts = path_parts[:-1]
      gpath_parts = path_parts[:-1]
      if len(path_parts) >= 5:
        prefix_parts = path_parts[3:5]
        gpath_parts = path_parts[:5]

      gpath = '/'.join(gpath_parts)
      shard_id = '_'.join(prefix_parts).strip().lower()[:63]
      if shard_id.startswith('pg_'):
        shard_id = '_' + shard_id[3:]

      shard_id = re.sub('^[^a-zA-Z_]', '_', shard_id, count=1)
      shard_id = re.sub('[^0-9a-zA-Z_]+', '_', shard_id)

      self.pg.psql('''drop schema if exists %s cascade''' % shard_id)
      self.pg.exec('''set -xeu;export GPATH="%s" && cd "$GSKY_MAS_SHARE_DIR" && bash ingest_pipeline.sh %s "%s"''' % (gpath, shard_id, f))

      print('%d of %d done' % (i+1, len(files)))
