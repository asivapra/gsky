import subprocess as sp
import os
import sys
import signal
import env_configs as cfg
import time
import requests

class Worker:
  def __init__(self, envs=None):
    if envs is None:
      self.envs = cfg.Enviornment().envs
    else:
      self.envs = envs
    
    assert 'GSKY_GRPC_POOL_SIZE' in self.envs
    self.is_init = False
    self.envs['GSKY_GRPC_POOL_SIZE'] = '32' # AVS

  def start_async(self):
    if not self.is_init:
      if 'TMPDIR' in self.envs:
        if not os.path.exists(self.envs['TMPDIR']):
          os.makedirs(self.envs['TMPDIR'])
      self.proc = sp.Popen('''(set -xeu
        cd "$GSKY_SHARE_DIR" && ./grpc_server -p $GSKY_GRPC_PORT -n $GSKY_GRPC_POOL_SIZE 
        )''', env=self.envs, shell=True, stdout=sys.stdout, stderr=sys.stderr, preexec_fn=os.setpgrp)

      self.is_init = True

  def start(self):
    self.start_async()

    pool_size = int(self.envs['GSKY_GRPC_POOL_SIZE'])

    worker_timeout = 30
    for i in range(worker_timeout):
      try:
        n_procs_str = sp.check_output('ps s|grep gdal-process|wc -l', shell=True, stderr=sys.stderr, universal_newlines=True).strip()
        n_procs = int(n_procs_str)
        # pool_size + 1 takes 'grep gdal-process' into account
        if n_procs >= pool_size + 1:
          return
      except:
        pass
      
      ret = self.proc.poll()     
      if ret is not None:
        self.is_init = False
        raise Exception('worker abnormally exited')

      time.sleep(1)

    raise Exception('worker startup timed out')
      
  def stop(self):
    if self.is_init:
      os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
