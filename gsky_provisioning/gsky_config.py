import os
import argparse
import yaml
import json
import env_configs as cfg

class GSKYConfig:
  def __init__(self,
      init_conf={
        'service_config':{
          'ows_hostname': '',
          'mas_address': '',
          'worker_nodes': [],
        },
      },
      section_key_id_map = {
        'layers': 'name',
        'processes': 'identifier',
      },
      subst_var_map={
        'GSKY_SHARE_DIR': 'gsky/share/gsky',
      },
      envs=None
    ):

    if envs is None:
      self.envs = cfg.Environment().envs
    else:
      self.envs = envs

    self.init_conf = init_conf

    if len(self.init_conf['service_config']['ows_hostname']) == 0:
      ows_hostname = 'http://localhost'
      if 'GSKY_OWS_HOSTNAME' in self.envs:
        ows_hostname = self.envs['GSKY_OWS_HOSTNAME']

      self.init_conf['service_config']['ows_hostname'] = ows_hostname

    if len(self.init_conf['service_config']['mas_address']) == 0:
      mas_port = '9512'
      if 'GSKY_MASAPI_PORT' in self.envs:
        mas_port = self.envs['GSKY_MASAPI_PORT']
      self.init_conf['service_config']['mas_address'] = 'localhost:%s' % mas_port

    if len(self.init_conf['service_config']['worker_nodes']) == 0:
      grpc_port = '9513'
      if 'GSKY_GRPC_PORT' in self.envs:
        grpc_port = self.envs['GSKY_GRPC_PORT']

      self.init_conf['service_config']['worker_nodes'] = ['localhost:%s' % grpc_port,]

    self.subst_var_map = subst_var_map
    gsky_share_dir = 'gsky/share/gsky'
    if 'GSKY_DATA_DIR' in self.envs:
      gsky_share_dir = self.envs['GSKY_DATA_DIR']

    self.subst_var_map['GSKY_SHARE_DIR'] = gsky_share_dir

    self.section_key_id_map = section_key_id_map

  def get_config(self, conf_file=''):
    result_dict = self.init_conf

    if conf_file:
      with open(conf_file) as f:
        result_dict.update(yaml.safe_load(f))
        config_root = os.path.dirname(conf_file)

      for sect_id, paths in result_dict.items():
        if sect_id in self.section_key_id_map:
          key_id = self.section_key_id_map[sect_id]
          result_dict[sect_id] = self.create_dict_list(key_id, paths, config_root, self.subst_var_map)

    return result_dict

  def get_config_json(self, conf_file='', indent=2):
    result_dict = self.get_config(conf_file)
    return json.dumps(result_dict, indent=indent)

  def subst_vars_walk_node(self, obj, i, token, sub_val):
    v = obj[i]
    if isinstance(v, dict) or isinstance(v, list) or isinstance(v, tuple):
      self.subst_vars_walk(v, token, sub_val)
    elif isinstance(v, str) and (token in v):
      obj[i] = v.replace(token, sub_val)

  def subst_vars_walk(self, obj, token, sub_val):
    if isinstance(obj, dict):
      for k in obj.keys():
        self.subst_vars_walk_node(obj, k, token, sub_val)
    else:
      assert isinstance(obj, list) or isinstance(obj, tuple)
      for i in range(len(obj)):
        self.subst_vars_walk_node(obj, i, token, sub_val)

  def create_dict_list(self, key_id, paths, config_root, sv_map):
    dict_list = []
    for path in paths:
      with open(os.path.join(config_root, path), 'r') as fh:
        item_map = yaml.safe_load(fh)
        for k, v in item_map.items():
          if k.startswith('.'):
            # Skip anchor templates
            continue

          v[key_id] = k

          for sn, sv in sv_map.items():
            token = '${' + sn + '}'
            self.subst_vars_walk(v, token, sv)

          dict_list.append(v)

    return dict_list


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('conf_file') 
  args = parser.parse_args()

  conf = GSKYConfig()
  result = conf.get_config_json(args.conf_file)
  print(result)
