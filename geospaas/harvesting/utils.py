"""Utilities module for geospaas.harvesting"""
import copy
import importlib
import os
import pkgutil
import re
import sys
import xml.etree.ElementTree as ET
from datetime import timedelta
from urllib.parse import urlparse

import requests
import yaml


def get_all_subclasses(base_class):
    """Recursively get all subclasses of `base_class`.
    Returns a set to ensure uniqueness
    """
    subclasses = set()
    for subclass in base_class.__subclasses__():
        subclasses.add(subclass)
        subclasses = subclasses.union(get_all_subclasses(subclass))
    return subclasses


def export_subclasses(package__all__, package_name, package_dir, base_class):
    """Append `base_class` and all of its subclasses declared in
    modules in `package_dir` to `all`. This is meant to be used in
    __init__.py files to make normalizer classes easily importable.
    """
    package__all__.append(base_class.__name__)

    # Import the modules in the package
    for (_, name, _) in pkgutil.iter_modules([package_dir]):
        importlib.import_module('.' + name, package_name)

    # Make the base_class subclasses available
    # in the 'package' namespace
    for cls in get_all_subclasses(base_class):
        setattr(sys.modules[package_name], cls.__name__, cls)
        package__all__.append(cls.__name__)

class TrustDomainSession(requests.Session):
    """Session class which allows keeping authentication headers in
    case of redirection to the same domain
    """

    def should_strip_auth(self, old_url, new_url):
        """Keep the authentication header when redirecting to a
        different host in the same domain, for example from
        "scihub.copernicus.eu" to "apihub.copernicus.eu".
        If not in this case, defer to the parent class.
        """
        old_split_hostname = urlparse(old_url).hostname.split('.')
        new_split_hostname = urlparse(new_url).hostname.split('.')
        if (len(old_split_hostname) == len(new_split_hostname) > 2
                and old_split_hostname[1:] == new_split_hostname[1:]):
            return False
        else:
            return super().should_strip_auth(old_url, new_url)


def http_request(http_method, *args, **kwargs):
    """Wrapper around requests.request() which runs the HTTP request
    inside a TrustDomainSession if authentication is provided. This
    makes it possible to follow redirections inside the same domain.
    """
    auth = kwargs.pop('auth', None)

    if auth:
        with TrustDomainSession() as session:
            session.auth = auth
            return session.request(http_method, *args, **kwargs)
    else:
        return requests.request(http_method, *args, **kwargs)


class EnvTag(yaml.YAMLObject):
    """class for reading the tags of yml file for finding the value of
    environment variables
    """
    yaml_tag = u'!ENV'

    @classmethod
    def from_yaml(cls, loader, node):
        return os.getenv(node.value)


def read_yaml_file(config_path):
    """Loads the harvesting configuration from a file"""
    yaml.SafeLoader.add_constructor('!ENV', EnvTag.from_yaml)
    data = None
    with open(config_path, 'rb') as config_stream:
        data = yaml.safe_load(config_stream)
    return data


def parse_xml_get_ns(file):
    """Parse an XML document and return an ElementTree and a dict of
    namespaces
    """
    events = "start", "start-ns"
    root = None
    namespaces = {}
    for event, elem in ET.iterparse(file, events):
        if event == "start-ns":
            if elem[0] in namespaces and namespaces[elem[0]] != elem[1]:
                raise KeyError("Duplicate prefix with different URI found.")
            namespaces[elem[0] if elem[0] else 'default'] = str(elem[1])
        elif event == "start":
            if root is None:
                root = elem
    return ET.ElementTree(root), namespaces


def mask_secrets(dictionary, secret_keys=('password',)):
    """Returns a copy of the dictionary, replacing the values of secret
    keys with '******'
    """
    masked = dictionary.copy()
    for key in secret_keys:
        if key in dictionary:
            masked[key] = '******'
    return masked


def merge_configs(config_dict: dict, override: dict):
    """Merge two configuration dictionaries.
    The values in `override` are added to `config_dict`.
    In case keys are present in both dicts:
    - if the value is a dict, update this dict with the values from
      `override`
    - otherwise, replace the values in `config_dict` by the ones from
      `override`
    For example:
        merge_configs(
            config_dict={
                'a': 1,
                'b': [2, 3],
                'c': {'d': 4, 'e': 5},
                'f': 6
            },
            override={
                'a': 10,
                'b': [20],
                'c': {'d':40}
            })
    results in:
        {
            'a': 10,
            'b': [20],
            'c': {'d': 40, 'e': 5},
            'f': 6
        }
    """
    final_config = copy.deepcopy(config_dict)
    for key in override:
        if key in final_config:
            if type(final_config[key]) == type(override[key]):
                if isinstance(final_config[key], dict):
                    final_config[key].update(override[key])
                else:
                    final_config[key] = override[key]
            else:
                raise ValueError(
                    f"'{key}' must have the same type in the "
                    "override")
        else:
            final_config[key] = override[key]
    return final_config


def parse_timedelta_str(timedelta_str: str) -> timedelta:
    """Parse a string in the format `?d?h?m?s`
    """
    groups = re.match(
        r'((?P<days>\d+)d)?((?P<hours>\d+)h)?((?P<minutes>\d+)m)?((?P<seconds>\d+)s)?',
        timedelta_str).groupdict()
    return timedelta(
        days=int(groups.get('days') or 0),
        hours=int(groups.get('hours') or 0),
        minutes=int(groups.get('minutes') or 0),
        seconds=int(groups.get('seconds') or 0))
