import argparse
import os

import django
import django.conf
# Load Django settings to be able to interact with the database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geospaas_web.settings')
if not django.conf.settings.configured:
    django.setup()  # pragma: no cover

from geospaas.config import plugins_manager


def make_arg_parser() -> argparse.ArgumentParser:
    """Create the main argument parser, with parsers from CLI plugins
    added as subparsers
    """
    parser = argparse.ArgumentParser(prog='geospaas', description='GeoSPaaS CLI')
    subparsers = parser.add_subparsers()
    for cli_plugin in plugins_manager.get_plugins_submodule('cli'):
        sub_parser:argparse.ArgumentParser = cli_plugin.make_arg_parser()
        subparsers.add_parser(sub_parser.prog, parents=[sub_parser], add_help=False)
    return parser


def main():
    parser = make_arg_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':  # pragma: no cover
    main()
