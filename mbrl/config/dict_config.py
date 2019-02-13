import json
import os
import typeguard as tg


class Config(object):
    pass


class DictConfig(Config):
    def __init__(self, required_key_dict: dict, config_dict=None, cls_name=""):
        self.cls_name = cls_name

        self.required_key_dict = required_key_dict
        if config_dict:
            self.config_dict = config_dict
        else:
            self._config_dict = {}

    @property
    def config_dict(self):
        return self._config_dict

    @config_dict.setter
    def config_dict(self, new_value):
        if self.check_config(dict=new_value, key_dict=self.required_key_dict) is True:
            for key, val in new_value.items():
                if type(val) is list:
                    new_value[str(key)] = tuple(val)
            self._config_dict = new_value
            # todo check this
            for key, val in self._config_dict.items():
                setattr(self, key, val)

    def save_config(self, path, name):
        DictConfig.save_to_json(dict=self.config_dict, path=path, file_name=name)

    def load_config(self, path):
        res = DictConfig.load_json(file_path=path)
        self.config_dict = res

    def check_config(self, dict: dict, key_dict: dict) -> bool:
        if self.check_dict_key(check_dict=dict, required_key_dict=key_dict):
            return True
        else:
            return False

    @staticmethod
    def load_json(file_path):
        with open(file_path, 'r') as f:
            res = json.load(f)
            return res

    @staticmethod
    def save_to_json(dict, path, file_name=None):
        if file_name is not None:
            path = os.path.join(path, file_name)
        with open(path, 'w') as f:
            json.dump(obj=dict, fp=f, indent=4, sort_keys=True)

    def check_dict_key(self, check_dict: dict, required_key_dict: dict) -> bool:
        for key, val in required_key_dict.items():
            if not isinstance(check_dict, dict):
                raise TypeError('{}: input check dict should be a dict instead of {}'.format(self.cls_name,
                                                                                             type(check_dict).__name__))
            if key not in check_dict:
                raise IndexError('{} Missing Key {}'.format(self.cls_name, key))
            if required_key_dict[key] is not None and not isinstance(check_dict[key], type(required_key_dict[key])):
                raise TypeError('{} should be type {} from required key dict file but with type {}'.
                                format(key, type(check_dict[key]), type(required_key_dict[key])))
            if isinstance(val, dict):
                self.check_dict_key(check_dict=check_dict[key], required_key_dict=required_key_dict[key])
        return True

    def __call__(self, key):
        if key not in self.config_dict:
            raise KeyError('{} key {} not in the config'.format(self.cls_name, key))
        else:
            return self.config_dict[key]

    def __getitem__(self, item):
        return self.__call__(item)