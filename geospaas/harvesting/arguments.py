"""This module defines classes used to parse and validate arguments.
"""
import copy
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import dateutil.parser
import shapely.wkt
from shapely.errors import GEOSException


class NoDefault:
    """Special class used when no default value is specified"""


class Argument():
    """Base class for arguments. Each argument has at least a name and
    a 'required' attribute.
    """
    type = 'unknown'

    def __init__(self, name='', **kwargs):
        self.name = name
        self.required = kwargs.get('required', False)
        self.default = kwargs.get('default', NoDefault)
        self.description = kwargs.get('description', '')

    def __eq__(self, other):
        return (
            self.name == other.name and
            self.required == other.required and
            self.default == other.default and
            self.description == other.description
        )

    def __str__(self):
        return ', '.join(filter(None, (
            f"{self.name}",
            f"type={self.type}",
            'required' if self.required else 'not required',
            f"default={self.default}" if self.default is not NoDefault else '',
            f"description={self.description}" if self.description else '',
        )))

    def parse(self, value):
        """Return a properly formatted value for the argument.
        If the input is not correct, should raise an exception
        """
        raise NotImplementedError()


class ArgumentParser(Argument):
    """Class capable of validating if a dictionary of parameters
    matches a list of argument definitions
    """

    def __init__(self, arguments, name='root', strict=True, **kwargs):
        """Set the list of valid arguments.
        If `strict` is True, only the defined arguments must be present
        in the parameters being validated. Otherwise, extra parameters
        are allowed
        """
        self.arguments = {}
        self.add_arguments(arguments)
        self.strict = strict
        super().__init__(name, **kwargs)

    def __str__(self):
        result = ['available arguments:']
        result.extend([str(arg) for arg in self.arguments.values()])
        return '\n\t'.join(result)

    def add_arguments(self, arguments):
        """Adds or updates Arguments in the valid arguments"""
        for arg in arguments:
            if not (isinstance(arg, Argument) or isinstance(arg, ArgumentParser)):
                raise ValueError(f"{arg} should be an Argument or ArgumentParser object")
            self.arguments[arg.name] = arg

    def parse(self, parameters, allow_missing=False):
        """Makes sure the right arguments are passed and parses them.
        `parameters` should be a dictionary of parameters to be
        validated.
        """
        parsed_parameters = {}
        recursion_stack = list(self.arguments.values())
        max_stack_size = 10000

        # Loop through the argument definitions and check that the
        # parameters match the definitions.
        while recursion_stack and len(recursion_stack) <= max_stack_size:
            # if the name of the argument is found in the parameters,
            # the value is parsed and adde to the final results.
            argument = recursion_stack.pop()
            if argument.name in parameters:
                parsed_parameters[argument.name] = argument.parse(
                    parameters.pop(argument.name))
            elif not allow_missing and argument.required:
                raise ValueError(f"Argument {argument.name} not provided")
            else:
                if argument.default is not NoDefault:
                    if isinstance(argument.default, type):
                        default = argument.default()
                    else:
                        # copy prevents all instances from sharing the
                        # same default object when the default is mutable
                        default = copy.deepcopy(argument.default)
                    parsed_parameters[argument.name] = default

        if self.strict and parameters:
            raise ValueError(f"Unknown argument(s) {parameters}")

        return parsed_parameters


class AnyArgument(Argument):
    """Passthrough argument with no validation"""
    type = 'any type'

    def parse(self, value):
        return value


class BooleanArgument(Argument):
    """Boolean argument. Should be an explicit boolean"""
    type = 'boolean'

    def parse(self, value):
        if isinstance(value, bool):
            return value
        else:
            raise ValueError(f"{self.name} should be a boolean")


class ChoiceArgument(Argument):
    """Validates that the value of the argument is included in a list
    of valid options
    """
    type = 'multiple choices'

    def __init__(self, name='', **kwargs):
        self.valid_options = kwargs.pop('valid_options', [])
        super().__init__(name, **kwargs)
        if self.default is not NoDefault:
            self.validate(self.default)

    def __eq__(self, other):
        return super().__eq__(other) and self.valid_options == other.valid_options

    def __str__(self):
        return super().__str__() + f", valid options={self.valid_options}"

    def validate(self, value):
        """Check if the value is valid. Returns a boolean"""
        if self.valid_options and value not in self.valid_options:
            raise ValueError(f"{value} is not a valid option for {self.name}")

    def parse(self, value):
        self.validate(value)
        return value


class DatetimeArgument(Argument):
    """Creates a Datetime from a string. If no timezone is specified,
    it is set as UTC.
    """
    type = 'datetime'

    def parse(self, value):
        if value is None:
            return None
        elif isinstance(value, datetime):
            _datetime = value
        else:
            _datetime = dateutil.parser.parse(value)

        if _datetime.tzinfo is None:
            _datetime = _datetime.replace(tzinfo=timezone.utc)
        return _datetime


class DictArgument(Argument):
    """Dictionary argument"""
    type = 'dictionary'

    def __init__(self, name='', **kwargs):
        self.valid_keys = set(kwargs.pop('valid_keys', []))
        self.values_types = kwargs.pop('values_types', [])
        super().__init__(name, **kwargs)

    def __eq__(self, other):
        return super().__eq__(other) and self.valid_keys == other.valid_keys

    def __str__(self):
        return (super().__str__() +
                (f", valid keys={self.valid_keys}" if self.valid_keys else ''))

    def parse(self, value):
        if not isinstance(value, dict):
            raise ValueError(f"{self.name} should be a dictionary")

        for dict_key, dict_value in value.items():
            if self.valid_keys and dict_key not in self.valid_keys:
                raise ValueError(f"Invalid key '{dict_key}'")
            valid = False
            if self.values_types:
                # self.values_types can contain Python types or
                # Argument instances
                for valid_type in self.values_types:
                    if isinstance(valid_type, Argument):
                        try:
                            valid_type.parse(dict_value)
                        except ValueError:
                            continue
                        else:
                            valid = True
                            break
                    elif isinstance(dict_value, valid_type):
                        valid = True
                        break
                if not valid:
                    raise ValueError(
                        f"The value for '{dict_key}' should be of one of the following types: " +
                        str(self.values_types))
        return value


class IntegerArgument(Argument):
    """Validates that the argument value is an integer, optionally
    comprised between a minimum and a maximum value
    """
    type = 'integer'

    def __init__(self, name='', **kwargs):
        min_value = kwargs.pop('min_value', None)
        max_value = kwargs.pop('max_value', None)
        self.min_value = int(min_value) if min_value is not None else min_value
        self.max_value = int(max_value) if max_value is not None else max_value
        super().__init__(name, **kwargs)

    def __eq__(self, other):
        return (
            super().__eq__(other) and
            self.min_value == other.min_value and
            self.max_value == other.max_value
        )

    def __str__(self):
        return (super().__str__() +
                (f", minimum value={self.min_value}" if self.min_value else '') +
                (f", maximum value={self.max_value}" if self.max_value else ''))

    def parse(self, value):
        if not isinstance(value, int):
            raise ValueError(f"{self.name} should be an integer")
        if (self.min_value is not None and value < self.min_value or
                self.max_value is not None and value > self.max_value):
            raise ValueError(
                f"{value} outside of allowed range: [{self.min_value}, {self.max_value}]")
        return value


class SequenceArgument(Argument):
    """The argument can be any sequence"""
    type = 'sequence'

    def __init__(self, name='', **kwargs):
        super().__init__(name, **kwargs)
        self.contents_type = kwargs.get('contents_type', AnyArgument) # should be an argument class
        self.length = kwargs.get('length', None)

    def parse(self, value):
        if not isinstance(value, Sequence):
            raise ValueError(f"{self.name} should be a sequence")
        if self.length is not None and len(value) != self.length:
            raise ValueError(f"{self.name} should have {self.length} elements")
        return type(value)(self.contents_type(f'{self.name} element').parse(elt) for elt in value)


class ListArgument(SequenceArgument):
    """Check that the value is a list"""
    type = 'list'

    def parse(self, value):
        if not isinstance(value, list):
            raise ValueError(f"{self.name} should be a list")
        return super().parse(value)


class PathArgument(ChoiceArgument):
    """Path argument with format validation and optional valid options.
    Only absolute paths are accepted.
    Subdirectories of the valid options are still valid.
    """
    type = 'path'

    def validate(self, value: Path):
        # check valid options
        if self.valid_options:
            found = False
            for valid_path in self.valid_options:
                if value.is_relative_to(valid_path):
                    found = True
                    break
            if not found:
                raise ValueError(
                    f"{value} is not an accepted path. Accepted paths are: {self.valid_options}")

    def parse(self, value):
        path_value = Path(value)
        self.validate(path_value)
        return path_value


class StringArgument(Argument):
    """String argument with optional regex validation"""
    type = 'string'

    def __init__(self, name='', **kwargs):
        self.regex = kwargs.pop('regex', None)
        super().__init__(name, **kwargs)

    def __eq__(self, other):
        return super().__eq__(other) and self.regex == other.regex

    def __str__(self):
        return (super().__str__() +
                (f", validation regex={self.regex}" if self.regex else ''))

    def parse(self, value):
        if not isinstance(value, str):
            raise ValueError(f"{self.name} should be a string")
        if self.regex is not None and not re.match(self.regex, value):
            raise ValueError(f"Value does not match the validation pattern {self.regex}")
        return value


class WKTArgument(Argument):
    """Creates a shapely geometry object from a WKT string"""
    type = 'WKT string'

    def __init__(self, name='', **kwargs):
        self.geometry_types = kwargs.pop('geometry_types', [])
        super().__init__(name, **kwargs)

    def __eq__(self, other):
        return super().__eq__(other) and self.geometry_types == other.geometry_types

    def __str__(self):
        accepted_geometries = [g.__name__ for g in self.geometry_types]
        return (super().__str__() +
                (f", accepted geometries={accepted_geometries}" if accepted_geometries else ''))

    def parse(self, value):
        geometry = shapely.wkt.loads(value)
        geometry_type = type(geometry)
        if not self.geometry_types or geometry_type in self.geometry_types:
            return geometry
        else:
            raise ValueError(f"{geometry_type} is not supported for argument {self.name}")


class WKTOrStringArgument(WKTArgument):
    """Creates a shapely geometry if possible. Otherwise, if the
    argument is a string, pass it through
    """
    type = 'WKT or arbitrary string'

    def parse(self, value):
        try:
            return super().parse(value)
        except GEOSException as error:
            return str(value)
