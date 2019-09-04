# -*- coding: utf-8 -*-
"""The source file classes."""

from __future__ import unicode_literals

import collections
import os

import source_code


class DefinitionsIncludeHeaderFile(object):
  """Definitions include header file.

  Attributes:
    enum_declarations (list[EnumDeclaration]): enumeration type declarations.
  """

  def __init__(self, path):
    """Initializes a definitions include header file.

    Args:
      path (str): path of the include header file.
    """
    super(DefinitionsIncludeHeaderFile, self).__init__()
    self._path = path

    self.definitions = []

  def Read(self, project_configuration):
    """Reads the include header file.

    Args:
      project_configuration (ProjectConfiguration): project configuration.
    """
    self.enum_declarations = []

    enum_prefix = b'enum '.format(
        project_configuration.library_name.upper())
    enum_prefix_length = len(enum_prefix)

    in_enum = False
    enum_declaration = None

    with open(self._path, 'rb') as file_object:
      for line in file_object.readlines():
        line = line.strip()

        if in_enum:
          if line.startswith(b'};'):
            in_enum = False

            self.enum_declarations.append(enum_declaration)
            enum_declaration = None

          elif not line.startswith(b'{'):
            definition, _, value = line.partition(b'=')

            definition = definition.strip()
            definition = definition.rstrip(b',')

            value = value.strip()
            value = value.rstrip(b',')

            enum_declaration.constants[definition] = value

        if line.startswith(enum_prefix):
          in_enum = True
          enum_declaration = source_code.EnumDeclaration(
              line[enum_prefix_length:])


class LibraryHeaderFile(object):
  """Library header file.

  Attributes:
    functions_per_name (dict[str, list[FunctionPrototype]]): function
        prototypes per name.
    have_internal_functions (bool): True if the header defines internal, non
        extern, functions.
    path (str): path of the header file.
    types (list[str]): type names.
  """

  def __init__(self, path):
    """Initializes a library header file.

    Args:
      path (str): path of the header file.
    """
    super(LibraryHeaderFile, self).__init__()
    self._library_name = None
    self.functions_per_name = collections.OrderedDict()
    self.have_internal_functions = False
    self.path = path
    self.types = []

  def _ReadFileObject(
      self, project_configuration, header_file_object, source_file_object):
    """Reads a header file-like object.

    Args:
      project_configuration (ProjectConfiguration): project configuration.
      header_file_object (file): header file-like object.
      source_file_object (file): source file-like object or None if not
          available.
    """
    self._library_name = project_configuration.library_name

    self.functions_per_name = collections.OrderedDict()
    self.types = []

    define_extern = b'{0:s}_EXTERN'.format(self._library_name.upper())

    define_have_debug_output = b'#if defined( HAVE_DEBUG_OUTPUT )'

    define_have_wide_character_type = (
        b'#if defined( HAVE_WIDE_CHARACTER_TYPE )')

    function_argument = None
    function_prototype = None
    have_extern = False
    have_debug_output = False
    have_wide_character_type = False
    in_function_prototype = False

    for line in header_file_object.readlines():
      line = line.strip()

      if in_function_prototype:
        line = line.decode('ascii')

        # Check if we have a callback function argument.
        if line.endswith('('):
          argument_string = '{0:s} '.format(line)
          function_argument = source_code.FunctionArgument(argument_string)

        else:
          if line.endswith(' );'):
            argument_string = line[:-3]

          else:
            # Get the part of the line before the ','.
            argument_string, _, _ = line.partition(',')

          if not function_argument:
            function_prototype.AddArgumentString(argument_string)

          else:
            function_argument.AddArgumentString(argument_string)

        if function_argument and line.endswith(' ),'):
          function_prototype.AddArgument(function_argument)
          function_argument = None

        elif line.endswith(' );'):
          self.functions_per_name[function_prototype.name] = (
              function_prototype)

          function_prototype = None
          in_function_prototype = False
          have_extern = False

      elif line.endswith(b'('):
        # Get the part of the line before the library name.
        data_type, _, _ = line.partition(self._library_name)

        # Get the part of the line after the data type.
        line = line[len(data_type):]
        data_type = data_type.strip()

        # Get the part of the remainder of the line before the '('.
        name, _, _ = line.partition('(')

        return_values = None
        value_description = None
        if source_file_object:
          ascii_name = name.encode('ascii')

          source_line = source_file_object.readline()
          while source_line:
            if source_line.startswith(b'/* Retrieves '):
              value_description = source_line.strip()
              value_description = value_description[13:]

              if value_description.startswith(b'a '):
                value_description = value_description[2:]

              elif value_description.startswith(b'an '):
                value_description = value_description[3:]

              elif value_description.startswith(b'the '):
                value_description = value_description[4:]

              if value_description.startswith(b'specific '):
                value_description = value_description[9:]

            elif source_line.startswith(b' * Returns '):
              return_values = set()
              if b' -1 ' in source_line:
                return_values.add('-1')
              if b' 0 ' in source_line:
                return_values.add('0')
              if b' 1 ' in source_line:
                return_values.add('1')
              if b' NULL ' in source_line:
                return_values.add('NULL')

            elif ascii_name in source_line:
              break

            source_line = source_file_object.readline()

        function_prototype = source_code.FunctionPrototype(name, data_type)
        function_prototype.have_extern = have_extern
        function_prototype.have_debug_output = have_debug_output
        function_prototype.have_wide_character_type = (
            have_wide_character_type)
        function_prototype.return_values = return_values
        function_prototype.value_description = value_description

        if not have_extern:
          self.have_internal_functions = True

        in_function_prototype = True

      elif line.startswith(define_extern):
        have_extern = True

      elif line.startswith(define_have_debug_output):
        have_debug_output = True

      elif line.startswith(define_have_wide_character_type):
        have_wide_character_type = True

      elif line.startswith(b'#endif'):
        have_debug_output = False
        have_wide_character_type = False

      elif line.startswith(b'typedef struct '):
        type_name = line.split(b' ')[2]
        self.types.append(type_name)

    self.types = sorted(self.types)

  def GetTypeFunction(self, type_name, type_function):
    """Retrieves the function prototype of a specific type function.

    Args:
      type_name (str): type name.
      type_function (str): type function.

    Returns:
      FunctionPrototype: function prototype of the type function or None
          if no such function.
    """
    function_name = '{0:s}_{1:s}_{2:s}'.format(
        self._library_name, type_name, type_function)
    return self.functions_per_name.get(function_name, None)

  def Read(self, project_configuration):
    """Reads a header file.

    Args:
      project_configuration (ProjectConfiguration): project configuration.
    """
    header_file_path = self.path
    if not os.path.exists(header_file_path):
      # Fallback to .h.in file if available.
      header_file_path = '{0:s}.in'.format(self.path)

    if not os.path.exists(header_file_path):
      raise IOError('Missing include header file: {0:s}'.format(self.path))

    source_file_path = '{0:s}.c'.format(self.path[:-2])
    with open(header_file_path, 'rb') as header_file_object:
      if os.path.exists(source_file_path):
        source_file_object = open(source_file_path, 'rb')
      else:
        source_file_object = None

      try:
        self._ReadFileObject(
            project_configuration, header_file_object, source_file_object)

      finally:
        if source_file_object:
          source_file_object.close()


class LibraryIncludeHeaderFile(object):
  """Library include header file.

  Attributes:
    functions_per_name (dict[str, list[FunctionPrototype]]): function
        prototypes per name.
    functions_per_section (dict[str, list[FunctionPrototype]]): function
        prototypes per section.
    have_bfio (bool): True if the include header supports libbfio.
    have_wide_character_type (bool): True if the include header supports
        the wide character type.
    name (str): name.
    section_names (list[str]): section names.
  """

  _SIGNATURE_TYPES = ('container', 'file', 'handle', 'store', 'volume')

  def __init__(self, path):
    """Initializes a library include header file.

    Args:
      path (str): path library include header file.
    """
    super(LibraryIncludeHeaderFile, self).__init__()
    self._api_functions_group = {}
    self._api_functions_with_input_group = {}
    self._api_pseudo_types_group = {}
    self._api_types_group = {}
    self._api_types_with_input_group = {}
    self._check_signature_type = None
    self._library_name = None
    self._path = path

    self.functions_per_name = collections.OrderedDict()
    self.functions_per_section = {}
    self.have_bfio = False
    self.have_wide_character_type = False
    self.name = os.path.basename(path)
    self.section_names = []

  def _AnalyzeFunctionGroups(self):
    """Analyzes the library include header file for function groups."""
    self._api_functions_group = {}
    self._api_functions_with_input_group = {}
    self._api_types_group = {}
    self._api_types_with_input_group = {}

    for section_name, functions in self.functions_per_section.items():
      if not functions:
        continue

      group_name = section_name.replace(' ', '_')
      group_name = group_name.replace('-', '_')
      group_name = group_name.lower()
      if '(' in group_name and ')' in group_name:
        prefix, _, suffix = group_name.partition('(')
        _, _, suffix = group_name.rpartition(')')
        group_name = ''.join([prefix[:-1], suffix])

      group_name, _, _ = group_name.rpartition('_functions')

      function_name_prefix = '{0:s}_{1:s}_'.format(
          self._library_name, group_name)

      found_match = False
      for function_prototype in functions:
        if function_prototype.name.startswith(function_name_prefix):
          found_match = True
          break

      # Ignore the section header if it is just informative.
      if not found_match:
        if group_name == 'support':
          signature_type = self.GetCheckSignatureType()
          if signature_type:
            self._api_functions_with_input_group[group_name] = section_name
          else:
            self._api_functions_group[group_name] = section_name

        else:
          # TODO: improve pseudo type detection.
          if group_name.endswith('_item'):
            group_name = group_name[:-5]

          function_name_prefix = '{0:s}_{1:s}_'.format(
              self._library_name, group_name)

          found_match = False
          for function_prototype in functions:
            if function_prototype.name.startswith(function_name_prefix):
              found_match = True
              break

          if found_match:
            self._api_pseudo_types_group[group_name] = section_name

      elif self._library_name != 'libcerror' and group_name == 'error':
        self._api_functions_group[group_name] = section_name

      elif (not self.HasTypeFunction(group_name, 'create') and
            not self.HasTypeFunction(group_name, 'free')):
        self._api_functions_group[group_name] = section_name

      elif not self.HasTypeFunction(group_name, 'open'):
        self._api_types_group[group_name] = section_name

      else:
        self._api_types_with_input_group[group_name] = section_name

  def GetAPIFunctionTestGroups(self):
    """Determines the API function test groups.

    Returns:
      tuple: contains:
        list[str]: names of API function groups without test data.
        list[str]: names of API function groups with test data.
    """
    if (not self._api_functions_group and
        not self._api_functions_with_input_group):
      self._AnalyzeFunctionGroups()

    return (
        self._api_functions_group.keys(),
        self._api_functions_with_input_group.keys())

  def GetAPIPseudoTypeTestGroups(self):
    """Determines the API pseudo type test groups.

    Returns:
      list[str]: names of API pseudo type groups without test data.
    """
    if not self._api_types_group and not self._api_types_with_input_group:
      self._AnalyzeFunctionGroups()

    return self._api_pseudo_types_group.keys()

  def GetAPITypeTestGroups(self):
    """Determines the API type test groups.

    Returns:
      tuple: contains:
        list[str]: names of API type groups without test data.
        list[str]: names of API type groups with test data.
    """
    if not self._api_types_group and not self._api_types_with_input_group:
      self._AnalyzeFunctionGroups()

    return self._api_types_group.keys(), self._api_types_with_input_group.keys()

  def GetCheckSignatureType(self):
    """Determines the check signature function type.

    Returns:
      str: check signature function type of None if no check signature function
          was found.
    """
    if not self._check_signature_type:
      for signature_type in self._SIGNATURE_TYPES:
        function_name = '{0:s}_check_{1:s}_signature'.format(
            self._library_name, signature_type)

        if function_name in self.functions_per_name:
          self._check_signature_type = signature_type
          break

    return self._check_signature_type

  def GetFunctionGroup(self, group_name):
    """Retrieves a function group.

    Args:
      group_name (str): group name.

    Returns:
      list[FunctionPrototype]: function prototypes of the functions in
          the group.
    """
    section_name = self._api_functions_group.get(group_name, None)
    if not section_name:
      section_name = self._api_functions_with_input_group.get(group_name, None)
    if not section_name:
      section_name = self._api_types_group.get(group_name, None)
    if not section_name:
      section_name = self._api_types_with_input_group.get(group_name, None)
    if not section_name:
      return []

    return self.functions_per_section.get(section_name, [])

  def HasErrorArgument(self, group_name):
    """Determines if a function group has functions with an error argument.

    Args:
      group_name (str): group name.

    Returns:
      bool: True if there ar functions with an error argument defined,
          False otherwise.
    """
    error_type = '{0:s}_error_t '.format(self._library_name)

    functions = self.GetFunctionGroup(group_name)
    for function_prototype in functions:
      if not function_prototype.arguments:
        continue

      function_argument = function_prototype.arguments[-1]
      function_argument_string = function_argument.CopyToString()
      if function_argument_string.startswith(error_type):
        return True

    return False

  def HasFunction(self, function_name):
    """Determines if the include header defines a specific function.

    Args:
      function_name (str): function name.

    Returns:
      bool: True if function is defined, False otherwise.
    """
    function_name = '{0:s}_{1:s}'.format(self._library_name, function_name)
    return function_name in self.functions_per_name

  def HasTypeFunction(self, type_name, type_function):
    """Determines if the include header defines a specific type function.

    Args:
      type_name (str): type name.
      type_function (str): type function.

    Returns:
      bool: True if function is defined, False otherwise.
    """
    function_name = '{0:s}_{1:s}_{2:s}'.format(
        self._library_name, type_name, type_function)
    return function_name in self.functions_per_name

  def Read(self, project_configuration):
    """Reads the include header file.

    Args:
      project_configuration (ProjectConfiguration): project configuration.
    """
    self._library_name = project_configuration.library_name

    self.functions_per_name = collections.OrderedDict()
    self.functions_per_section = {}
    self.have_bfio = False
    self.have_wide_character_type = False
    self.section_names = []

    define_deprecated = b'{0:s}_DEPRECATED'.format(self._library_name.upper())

    define_extern = b'{0:s}_EXTERN'.format(self._library_name.upper())

    define_have_bfio = b'#if defined( {0:s}_HAVE_BFIO )'.format(
        self._library_name.upper())

    define_have_debug_output = b'#if defined( HAVE_DEBUG_OUTPUT )'

    define_have_wide_character_type = (
        b'#if defined( {0:s}_HAVE_WIDE_CHARACTER_TYPE )').format(
            self._library_name.upper())

    function_argument = None
    function_prototype = None
    have_bfio = False
    have_extern = False
    have_debug_output = False
    have_wide_character_type = False
    in_define_deprecated = False
    in_section = False
    section_name = None

    with open(self._path, 'rb') as file_object:
      for line in file_object.readlines():
        line = line.strip()

        if have_extern:
          line = line.decode('ascii')

          if function_prototype:
            # Check if we have a callback function argument.
            if line.endswith('('):
              argument_string = '{0:s} '.format(line)
              function_argument = source_code.FunctionArgument(argument_string)

            else:
              if line.endswith(' );'):
                argument_string = line[:-3]

              else:
                # Get the part of the line before the ','.
                argument_string, _, _ = line.partition(',')

              if not function_argument:
                function_prototype.AddArgumentString(argument_string)

              else:
                function_argument.AddArgumentString(argument_string)

            if function_argument and line.endswith(' ),'):
              function_prototype.AddArgument(function_argument)
              function_argument = None

            elif line.endswith(' );'):
              if not in_define_deprecated:
                # TODO: handle section_name is None
                self.functions_per_name[function_prototype.name] = (
                    function_prototype)

                self.functions_per_section[section_name].append(
                    function_prototype)

              function_prototype = None
              in_define_deprecated = False
              have_extern = False

          elif line.endswith(';'):
            # The line contains a variable definition.
            have_extern = False

          else:
            # Get the part of the line before the library name.
            data_type, _, _ = line.partition(self._library_name)

            # Get the part of the line after the data type.
            line = line[len(data_type):]
            data_type = data_type.strip()

            # Get the part of the remainder of the line before the '('.
            name, _, _ = line.partition('(')

            function_prototype = source_code.FunctionPrototype(name, data_type)
            function_prototype.have_bfio = have_bfio
            function_prototype.have_extern = have_extern
            function_prototype.have_debug_output = have_debug_output
            function_prototype.have_wide_character_type = (
                have_wide_character_type)

            if have_bfio:
              self.have_bfio = True
            if have_wide_character_type:
              self.have_wide_character_type = True

        elif in_section:
          if line.startswith(b'* '):
            section_name = line[2:]
            self.section_names.append(section_name)
            self.functions_per_section[section_name] = []
            in_section = False

        elif line == (
            b'/* -------------------------------------------------------------'
            b'------------'):
          in_section = True

        elif line.startswith(define_deprecated):
          in_define_deprecated = True

        elif line.startswith(define_have_bfio):
          have_bfio = True

        elif line.startswith(define_extern):
          have_extern = True

        elif line.startswith(define_have_debug_output):
          have_debug_output = True

        elif line.startswith(define_have_wide_character_type):
          have_wide_character_type = True

        elif line.startswith(b'#endif'):
          have_bfio = False
          have_debug_output = False
          have_wide_character_type = False


class LibraryMakefileAMFile(object):
  """Library Makefile.am file.

  Attributes:
    cppflags (list[str]): C preprocess flags.
    libraries (list[str]): library names.
    sources (list[str]): source and header file paths.
  """

  def __init__(self, path):
    """Initializes a library Makefile.am file.

    Args:
      path (str): path of the Makefile.am file.
    """
    super(LibraryMakefileAMFile, self).__init__()
    self._library_name = None
    self._path = path
    self.cppflags = []
    self.libraries = []
    self.sources = []

  def Read(self, project_configuration):
    """Reads the Makefile.am file.

    Args:
      project_configuration (ProjectConfiguration): project configuration.
    """
    self._library_name = project_configuration.library_name

    self.cppflags = []
    self.libraries = []
    self.sources = []

    library_sources = b'{0:s}_la_SOURCES'.format(self._library_name)
    library_libadd = b'{0:s}_la_LIBADD'.format(self._library_name)

    in_section = None

    with open(self._path, 'rb') as file_object:
      for line in file_object.readlines():
        line = line.strip()

        if in_section:
          if not line:
            in_section = None
            continue

          if line.endswith(b'\\'):
            line = line[:-1].strip()

          if (in_section == 'cppflags' and line.startswith(b'@') and
              line.endswith(b'_CPPFLAGS@')):
            self.cppflags.append(line[1:-10].lower())

          elif (in_section == 'libadd' and line.startswith(b'@') and
                line.endswith(b'_LIBADD@')):
            self.libraries.append(line[1:-8].lower())

          elif in_section == 'sources':
            sources = line.split(b' ')
            self.sources.extend(sources)

        elif line == b'AM_CPPFLAGS = \\':
          in_section = 'cppflags'

        elif line.startswith(library_libadd):
          in_section = 'libadd'

        elif line.startswith(library_sources):
          in_section = 'sources'


class MainMakefileAMFile(object):
  """Main Makefile.am file.

  Attributes:
    libraries (list[str]): library names.
    library_dependencies (list[str]): names of the dependencies of the main
        library.
    tools_dependencies (list[str]): names of the dependencies of the tools.
  """

  def __init__(self, path):
    """Initializes a main Makefile.am file.

    Args:
      path (str): path of the Makefile.am file.
    """
    super(MainMakefileAMFile, self).__init__()
    self._library_name = None
    self._path = path
    self.libraries = []
    self.library_dependencies = []
    self.tools_dependencies = []

  def Read(self, project_configuration):
    """Reads the Makefile.am file.

    Args:
      project_configuration (ProjectConfiguration): project configuration.
    """
    self._library_name = project_configuration.library_name

    in_subdirs = False
    in_library_dependencies = True

    with open(self._path, 'rb') as file_object:
      for line in file_object.readlines():
        line = line.strip()

        if in_subdirs:
          if line.endswith(b'\\'):
            line = line[:-1].strip()

          if not line:
            in_subdirs = False

          elif line.startswith(b'lib'):
            if line == self._library_name:
              in_library_dependencies = False
            else:
              self.libraries.append(line)

              if in_library_dependencies:
                self.library_dependencies.append(line)
              else:
                self.tools_dependencies.append(line)

        elif line.startswith(b'SUBDIRS'):
          in_subdirs = True


class TypesIncludeHeaderFile(object):
  """Types include header file.

  Attributes:
    types (list[str]): type names.
  """

  def __init__(self, path):
    """Initializes a types include header file.

    Args:
      path (str): path of the include header file.
    """
    super(TypesIncludeHeaderFile, self).__init__()
    self._library_name = None
    self._path = path
    self.types = []

  def Read(self, project_configuration):
    """Reads the include header file.

    Args:
      project_configuration (ProjectConfiguration): project configuration.
    """
    self._library_name = project_configuration.library_name

    self.types = []

    typedef_prefix = b'typedef intptr_t {0:s}_'.format(self._library_name)
    typedef_prefix_length = len(typedef_prefix)

    with open(self._path, 'rb') as file_object:
      for line in file_object.readlines():
        line = line.strip()
        if line.startswith(typedef_prefix) and line.endswith(b'_t;'):
          self.types.append(line[typedef_prefix_length:-3])