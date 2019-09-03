import subprocess as sp
import os
import sys
import signal
import env_configs as cfg
import time
import requests

class OWS:
  def __init__(self, envs=None):
    if envs is None:
      self.envs = cfg.Environment().envs
    else:
      self.envs = envs
    
    self.is_init = False

  def start_async(self):
    if not self.is_init:
      self.proc = sp.Popen('''(set -xeu
        ows -p $GSKY_OWS_PORT -data_dir "$GSKY_DATA_DIR" -conf_dir "$GSKY_CONF_DIR"
        )''', env=self.envs, shell=True, stdout=sys.stdout, stderr=sys.stderr, preexec_fn=os.setpgrp)

      self.is_init = True

  def start(self):
    self.start_async()
    ows_url = 'http://localhost'
    if 'GSKY_OWS_HOSTNAME' in self.envs:
      ows_url = self.envs['GSKY_OWS_HOSTNAME']

    ows_timeout = 180
    if 'GSKY_OWS_STARTUP_TIMEOUT' in self.envs:
      ows_timeout = int(self.envs['GSKY_OWS_STARTUP_TIMEOUT'])

    for i in range(ows_timeout):
      try:
        res = requests.get(ows_url)
        if res.status_code == 200:
          return
      except:
        pass
      
      ret = self.proc.poll()     
      if ret is not None:
        self.is_init = False
        raise Exception('ows abornally exited')

      time.sleep(1)

    raise Exception('ows startup timed out')
      
  def stop(self):
    if self.is_init:
      os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
