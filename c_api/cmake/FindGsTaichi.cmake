#[=======================================================================[.rst:
FindGsTaichi
----------

Finds the GsTaichi library.

The module first attempts to locate ``GsTaichiConfig.cmake`` in any GsTaichi
installation in CMake variable ``GSTAICHI_C_API_INSTALL_DIR`` or environment
variable of the same name. If the config file cannot be found, the libraries are
heuristically searched by names and paths in ``GSTAICHI_C_API_INSTALL_DIR``.

Imported Targets
^^^^^^^^^^^^^^^^

This module provides the following imported targets, if found:

``GsTaichi::Runtime``
  The GsTaichi Runtime library.

Result Variables
^^^^^^^^^^^^^^^^

This will define the following variables:

``GsTaichi_FOUND``
  True if a GsTaichi installation is found.
``GsTaichi_VERSION``
  Version of installed GsTaichi. Components might have lower version numbers.
``GsTaichi_INCLUDE_DIRS``
  Paths to Include directories needed to use GsTaichi.
``GsTaichi_LIBRARIES``
  Paths to GsTaichi linking libraries (``.libs``).
``GsTaichi_REDIST_LIBRARIES``
  Paths to GsTaichi redistributed runtime libraries (``.so`` and ``.dll``). You
  might want to copy them next to your executables.

Cache Variables
^^^^^^^^^^^^^^^

The following cache variables may also be set:

``GsTaichi_Runtime_VERSION``
  GsTaichi runtime library version.
``GsTaichi_Runtime_INCLUDE_DIR``
  The directory containing ``gstaichi/gstaichi.h``.
``GsTaichi_Runtime_LIBRARY``
  Path to linking library of ``GsTaichi_Runtime``.
``GsTaichi_Runtime_REDIST_LIBRARY``
  Path to redistributed runtime library of ``GsTaichi_Runtime``.

#]=======================================================================]

cmake_policy(PUSH)

# Support `IN_LIST` in CMake `if` command.
if(POLICY CMP0057)
    cmake_policy(SET CMP0057 NEW)
endif()

find_package(Python QUIET COMPONENTS Interpreter)

# Find TiRT in the installation directory. The installation directory is
# traditionally specified by an environment variable
# `GSTAICHI_C_API_INSTALL_DIR`.
if(NOT EXISTS "${GSTAICHI_C_API_INSTALL_DIR}")
    message("-- Looking for GsTaichi libraries via environment variable GSTAICHI_C_API_INSTALL_DIR")
    set(GSTAICHI_C_API_INSTALL_DIR $ENV{GSTAICHI_C_API_INSTALL_DIR})
endif()
# New installation location after 2022-03-11.
if(NOT EXISTS "${GSTAICHI_C_API_INSTALL_DIR}" AND EXISTS "${Python_EXECUTABLE}")
    message("-- Looking for GsTaichi libraries via Python package installation (v2)")
    execute_process(COMMAND ${Python_EXECUTABLE} -c "import sys; import pathlib; print([pathlib.Path(x + '/gstaichi/_lib/c_api').resolve() for x in sys.path if pathlib.Path(x + '/gstaichi/_lib/c_api').exists()][0], end='')" OUTPUT_VARIABLE GSTAICHI_C_API_INSTALL_DIR)
endif()
# If the user didn't specity the environment variable, try find the C-API
# library in Python wheel.
if(NOT EXISTS "${GSTAICHI_C_API_INSTALL_DIR}" AND EXISTS "${Python_EXECUTABLE}")
    message("-- Looking for GsTaichi libraries via Python package installation")
    execute_process(COMMAND ${Python_EXECUTABLE} -c "import sys; import pathlib; print([pathlib.Path(x + '/../../../c_api').resolve() for x in sys.path if pathlib.Path(x + '/../../../c_api').exists()][0], end='')" OUTPUT_VARIABLE GSTAICHI_C_API_INSTALL_DIR)
endif()
message("-- GSTAICHI_C_API_INSTALL_DIR=${GSTAICHI_C_API_INSTALL_DIR}")
if(EXISTS "${GSTAICHI_C_API_INSTALL_DIR}")
    get_filename_component(GSTAICHI_C_API_INSTALL_DIR "${GSTAICHI_C_API_INSTALL_DIR}" ABSOLUTE)
    set(GSTAICHI_C_API_INSTALL_DIR "${GSTAICHI_C_API_INSTALL_DIR}" CACHE PATH "Root directory to GsTaichi installation")
else()
    message(WARNING "-- GSTAICHI_C_API_INSTALL_DIR doesn't point to a valid GsTaichi installation; configuration is very likely to fail")
endif()

# Set up default find components
if(TRUE)
    # (penguinliong) Currently we only have GsTaichi Runtime. We might make the
    # codegen a library in the future?
    set(GsTaichi_FIND_COMPONENTS "Runtime")
endif()

message("-- Looking for GsTaichi components: ${GsTaichi_FIND_COMPONENTS}")

# (penguinliong) Note that the config files only exposes libraries and their
# public headers. We still need to encapsulate the libraries into semantical
# CMake targets in this list. So please DO NOT find GsTaichi in config mode
# directly.
find_package(GsTaichi CONFIG QUIET HINTS "${GSTAICHI_C_API_INSTALL_DIR}")

if(GsTaichi_FOUND)
    message("-- Found GsTaichi ${GsTaichi_VERSION} in config mode: ${GsTaichi_DIR}")
else()
    message("-- Could NOT find GsTaichi in config mode; fallback to heuristic search")
endif()

# - [GsTaichi::Runtime] ----------------------------------------------------------

if(("Runtime" IN_LIST GsTaichi_FIND_COMPONENTS) AND (NOT TARGET GsTaichi::Runtime))
    if(GsTaichi_FOUND)
        if(NOT TARGET gstaichi_c_api)
            message(FATAL_ERROR "gstaichi is marked found but target gstaichi_c_api doesn't exists")
        endif()

        # Already found in config mode.
        get_target_property(GsTaichi_Runtime_CONFIG gstaichi_c_api IMPORTED_CONFIGURATIONS)
        if(${CMAKE_SYSTEM_NAME} STREQUAL Windows)
            get_target_property(GsTaichi_Runtime_LIBRARY gstaichi_c_api IMPORTED_IMPLIB)
        else()
            get_target_property(GsTaichi_Runtime_LIBRARY gstaichi_c_api LOCATION)
        endif()
        get_target_property(GsTaichi_Runtime_REDIST_LIBRARY gstaichi_c_api LOCATION)
        get_target_property(GsTaichi_Runtime_INCLUDE_DIR gstaichi_c_api INTERFACE_INCLUDE_DIRECTORIES)
    else()
        find_library(GsTaichi_Runtime_LIBRARY
            NAMES gstaichi_runtime gstaichi_c_api
            HINTS ${GSTAICHI_C_API_INSTALL_DIR}
            PATH_SUFFIXES lib
            # CMake find root is overriden by Android toolchain.
            NO_CMAKE_FIND_ROOT_PATH)

        find_library(GsTaichi_Runtime_REDIST_LIBRARY
            NAMES gstaichi_runtime gstaichi_c_api
            HINTS ${GSTAICHI_C_API_INSTALL_DIR}
            PATH_SUFFIXES bin lib
            # CMake find root is overriden by Android toolchain.
            NO_CMAKE_FIND_ROOT_PATH)

        find_path(GsTaichi_Runtime_INCLUDE_DIR
            NAMES gstaichi/gstaichi.h
            HINTS ${GSTAICHI_C_API_INSTALL_DIR}
            PATH_SUFFIXES include
            NO_CMAKE_FIND_ROOT_PATH)
    endif()

    # Capture GsTaichi Runtime version from header definition.
    if(EXISTS "${GsTaichi_Runtime_INCLUDE_DIR}/gstaichi/gstaichi_core.h")
        file(READ "${GsTaichi_Runtime_INCLUDE_DIR}/gstaichi/gstaichi_core.h" GsTaichi_Runtime_VERSION_LITERAL)
        string(REGEX MATCH "#define TI_C_API_VERSION ([0-9]+)" GsTaichi_Runtime_VERSION_LITERAL ${GsTaichi_Runtime_VERSION_LITERAL})
        set(GsTaichi_Runtime_VERSION_LITERAL ${CMAKE_MATCH_1})
        math(EXPR GsTaichi_Runtime_VERSION_MAJOR "${GsTaichi_Runtime_VERSION_LITERAL} / 1000000")
        math(EXPR GsTaichi_Runtime_VERSION_MINOR "(${GsTaichi_Runtime_VERSION_LITERAL} / 1000) % 1000")
        math(EXPR GsTaichi_Runtime_VERSION_PATCH "${GsTaichi_Runtime_VERSION_LITERAL} % 1000")
        set(GsTaichi_Runtime_VERSION "${GsTaichi_Runtime_VERSION_MAJOR}.${GsTaichi_Runtime_VERSION_MINOR}.${GsTaichi_Runtime_VERSION_PATCH}")
    endif()

    # Ensure the version string is valid.
    if("${GsTaichi_Runtime_VERSION}" VERSION_GREATER "0")
        message("-- Found GsTaichi Runtime ${GsTaichi_Runtime_VERSION}: ${GsTaichi_Runtime_LIBRARY}")

        add_library(GsTaichi::Runtime UNKNOWN IMPORTED)
        set_target_properties(GsTaichi::Runtime PROPERTIES
            IMPORTED_LOCATION "${GsTaichi_Runtime_LIBRARY}"
            INTERFACE_INCLUDE_DIRECTORIES "${GsTaichi_Runtime_INCLUDE_DIR}")

        list(APPEND COMPONENT_VARS
            GsTaichi_Runtime_REDIST_LIBRARY
            GsTaichi_Runtime_LIBRARY
            GsTaichi_Runtime_INCLUDE_DIR)
        list(APPEND GsTaichi_LIBRARIES "${GsTaichi_Runtime_LIBRARY}")
        if(EXISTS ${GsTaichi_Runtime_REDIST_LIBRARY})
            list(APPEND GsTaichi_REDIST_LIBRARIES "${GsTaichi_Runtime_REDIST_LIBRARY}")
        endif()
        list(APPEND GsTaichi_INCLUDE_DIRS "${GsTaichi_Runtime_INCLUDE_DIR}")
    endif()
endif()

# - [gstaichi] -------------------------------------------------------------------

# Handle `QUIET` and `REQUIRED` args in the recommended way in `find_package`.
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(GsTaichi DEFAULT_MSG ${COMPONENT_VARS})
set(GsTaichi_VERSION ${GsTaichi_Runtime_VERSION})
set(GsTaichi_INCLUDE_DIRS ${GsTaichi_INCLUDE_DIRS})
set(GsTaichi_LIBRARIES ${GsTaichi_LIBRARIES})
set(GsTaichi_REDIST_LIBRARIES ${GsTaichi_REDIST_LIBRARIES})

set(GsTaichi_Runtime_VERSION ${GsTaichi_Runtime_VERSION})
set(GsTaichi_Runtime_INCLUDE_DIR ${GsTaichi_Runtime_INCLUDE_DIR})
set(GsTaichi_Runtime_LIBRARY ${GsTaichi_Runtime_LIBRARY})
set(GsTaichi_Runtime_REDIST_LIBRARY ${GsTaichi_Runtime_REDIST_LIBRARY})


cmake_policy(POP)
