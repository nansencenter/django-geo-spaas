import argparse

from geospaas.config import get_plugins_cli


def make_arg_parser() -> argparse.ArgumentParser:
    """Create the main argument parser, with parsers from CLI plugins
    added as subparsers
    """
    parser = argparse.ArgumentParser(prog='geospaas', description='GeoSPaaS CLI')
    subparsers = parser.add_subparsers()
    for cli_plugin in get_plugins_cli():
        sub_parser:argparse.ArgumentParser = cli_plugin.make_arg_parser()
        subparsers.add_parser(sub_parser.prog, parents=[sub_parser], add_help=False)
    return parser


def main():
    """"""
    parser = make_arg_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':  # pragma: no cover
    main()