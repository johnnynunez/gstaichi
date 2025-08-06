cmake_minimum_required(VERSION 3.11)

# This function creates a static target from OBJECT_TARGET, then link TARGET with the static target
#
# For now, we have to keep this hack because:
# 1. Existence of circular dependencies in GsTaichi repo (https://github.com/taichi-dev/gstaichi/issues/6838)
# 2. Link order restriction from `ld` linker on Linux (https://stackoverflow.com/questions/45135/why-does-the-order-in-which-libraries-are-linked-sometimes-cause-errors-in-gcc), which has zero-tolerance w.r.t circular dependencies.
function(target_link_static_library TARGET OBJECT_TARGET)
    set(STATIC_TARGET "${OBJECT_TARGET}_static")
    add_library(${STATIC_TARGET})
    target_link_libraries(${STATIC_TARGET} PUBLIC ${OBJECT_TARGET})
if(LINUX)
    get_target_property(LINK_LIBS ${OBJECT_TARGET} LINK_LIBRARIES)
    target_link_libraries(${TARGET} PRIVATE "-Wl,--start-group" "${STATIC_TARGET}" "${LINK_LIBS}" "-Wl,--end-group")
else()
    target_link_libraries(${TARGET} PRIVATE "${STATIC_TARGET}")
endif()
endfunction()

set(GSTAICHI_C_API_NAME gstaichi_c_api)
list(APPEND C_API_SOURCE "c_api/src/gstaichi_core_impl.cpp")
list(APPEND C_API_PUBLIC_HEADERS
  "c_api/include/gstaichi/gstaichi_platform.h"
  "c_api/include/gstaichi/gstaichi_core.h"
  "c_api/include/gstaichi/gstaichi.h"
  # FIXME: (penguinliong) Remove this in the future when we have a option for
  # Unity3D integration?
  "c_api/include/gstaichi/gstaichi_unity.h"
  )

if (TI_WITH_LLVM)
  list(APPEND C_API_SOURCE "c_api/src/gstaichi_llvm_impl.cpp")
  list(APPEND C_API_PUBLIC_HEADERS "c_api/include/gstaichi/gstaichi_cpu.h")

  if (TI_WITH_CUDA)
    list(APPEND C_API_PUBLIC_HEADERS "c_api/include/gstaichi/gstaichi_cuda.h")
  endif()
endif()

if (TI_WITH_OPENGL OR TI_WITH_VULKAN OR TI_WITH_METAL)
  list(APPEND C_API_SOURCE "c_api/src/gstaichi_gfx_impl.cpp")
endif()

if (TI_WITH_OPENGL)
  list(APPEND C_API_SOURCE "c_api/src/gstaichi_opengl_impl.cpp")
  list(APPEND C_API_PUBLIC_HEADERS "c_api/include/gstaichi/gstaichi_opengl.h")
endif()

if (TI_WITH_METAL)
  list(APPEND C_API_SOURCE "c_api/src/gstaichi_metal_impl.mm")
  list(APPEND C_API_PUBLIC_HEADERS "c_api/include/gstaichi/gstaichi_metal.h")
endif()

if (TI_WITH_VULKAN)
  list(APPEND C_API_SOURCE "c_api/src/gstaichi_vulkan_impl.cpp")
  list(APPEND C_API_PUBLIC_HEADERS "c_api/include/gstaichi/gstaichi_vulkan.h")
  if (APPLE)
    install(FILES ${MoltenVK_LIBRARY} DESTINATION c_api/lib)
  endif()
endif()

if(TI_BUILD_TESTS)
  list(APPEND C_API_SOURCE "c_api/src/c_api_test_utils.cpp")
endif()

add_library(${GSTAICHI_C_API_NAME} SHARED ${C_API_SOURCE})
if (${CMAKE_GENERATOR} STREQUAL "Xcode")
  target_link_libraries(${GSTAICHI_C_API_NAME} PRIVATE gstaichi_core)
  message(WARNING "Static wrapping does not work on Xcode, using object linking instead.")
elseif (MSVC)
  target_link_libraries(${GSTAICHI_C_API_NAME} PRIVATE gstaichi_core)
else()
  target_link_static_library(${GSTAICHI_C_API_NAME} gstaichi_core)
endif()
target_enable_function_level_linking(${GSTAICHI_C_API_NAME})

# Strip shared library
set_target_properties(${GSTAICHI_C_API_NAME} PROPERTIES LINK_FLAGS_RELEASE -s)


# Avoid exporting third party symbols from libgstaichi_c_api.so
# Note that on Windows, external symbols will be excluded from .dll automatically, by default.
if(LINUX)
    target_link_options(${GSTAICHI_C_API_NAME} PRIVATE -Wl,--version-script,${CMAKE_CURRENT_SOURCE_DIR}/c_api/version_scripts/export_symbols_linux.lds)
    if (NOT ANDROID)
        target_link_options(${GSTAICHI_C_API_NAME} PRIVATE -static-libgcc -static-libstdc++)
    endif()
elseif(APPLE)
    # Unfortunately, ld on MacOS does not support --exclude-libs and we have to manually specify the exported symbols
    target_link_options(${GSTAICHI_C_API_NAME} PRIVATE -Wl,-exported_symbols_list,${CMAKE_CURRENT_SOURCE_DIR}/c_api/version_scripts/export_symbols_mac.lds)
endif()

target_include_directories(${GSTAICHI_C_API_NAME}
    PUBLIC
        # Used when building the library:
        $<BUILD_INTERFACE:${gstaichi_c_api_BINARY_DIR}/c_api/include>
        $<BUILD_INTERFACE:${gstaichi_c_api_SOURCE_DIR}/c_api/include>
        # Used when installing the library:
        $<INSTALL_INTERFACE:c_api/include>
    PRIVATE
        # Used only when building the library:
        ${PROJECT_SOURCE_DIR}
        ${PROJECT_SOURCE_DIR}/c_api/include
        ${CMAKE_CURRENT_SOURCE_DIR}/external/spdlog/include
        ${CMAKE_CURRENT_SOURCE_DIR}/external/Vulkan-Headers/include
        ${CMAKE_CURRENT_SOURCE_DIR}/external/VulkanMemoryAllocator/include
        ${CMAKE_CURRENT_SOURCE_DIR}/external/volk
        ${CMAKE_CURRENT_SOURCE_DIR}/external/glad/include
        ${CMAKE_CURRENT_SOURCE_DIR}/external/glfw/include
    )
set_property(TARGET ${GSTAICHI_C_API_NAME} PROPERTY PUBLIC_HEADER ${C_API_PUBLIC_HEADERS})

# This helper provides us standard locations across Linux/Windows/MacOS
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

function(install_gstaichi_c_api INSTALL_NAME GSTAICHI_C_API_INSTALL_DIR)

  # (penguinliong) This is the `CMAKE_INSTALL_PREFIX` from command line.
  set(CMAKE_INSTALL_PREFIX_BACKUP ${CMAKE_INSTALL_PREFIX})
  # This thing is read by `install(EXPORT ...)` to generate `_IMPORT_PREFIX` in
  # `GsTaichiTargets.cmake`. Replace the original value to avoid the absolute
  # path.
  set(CMAKE_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX_BACKUP}/${GSTAICHI_C_API_INSTALL_DIR})

  message("Installing to ${CMAKE_INSTALL_PREFIX}")

  install(TARGETS ${GSTAICHI_C_API_NAME} EXPORT GsTaichiExportTargets${INSTALL_NAME}
      LIBRARY DESTINATION ${GSTAICHI_C_API_INSTALL_DIR}/${CMAKE_INSTALL_LIBDIR}
      ARCHIVE DESTINATION ${GSTAICHI_C_API_INSTALL_DIR}/${CMAKE_INSTALL_LIBDIR}
      RUNTIME DESTINATION ${GSTAICHI_C_API_INSTALL_DIR}/${CMAKE_INSTALL_BINDIR}
      PUBLIC_HEADER DESTINATION ${GSTAICHI_C_API_INSTALL_DIR}/${CMAKE_INSTALL_INCLUDEDIR}/gstaichi
      )

  # The C++ wrapper is saved in a dedicated directory.
  install(
      FILES
          "c_api/include/gstaichi/cpp/gstaichi.hpp"
      DESTINATION
          ${GSTAICHI_C_API_INSTALL_DIR}/${CMAKE_INSTALL_INCLUDEDIR}/gstaichi/cpp
  )

  # Install the target script.
  # 2023-03-23 (penguinliong) We used to generate this by `install(EXPORT ...)`
  # but the generated content is generally uncontrollable so we turn to a hand
  # written script instead. CMake is really something.
  install(
      FILES
          "cmake/GsTaichiTargets.cmake"
      DESTINATION
          ${GSTAICHI_C_API_INSTALL_DIR}/gstaichi/${CMAKE_INSTALL_LIBDIR}/cmake/gstaichi
  )

  # Generate the config file. Put it to the same dir as `GsTaichiTargets.cmake`.
  configure_package_config_file(
          "${PROJECT_SOURCE_DIR}/cmake/GsTaichiConfig.cmake.in"
          "${PROJECT_BINARY_DIR}/GsTaichiConfig.cmake"
      INSTALL_DESTINATION
          ${GSTAICHI_C_API_INSTALL_DIR}/gstaichi/${CMAKE_INSTALL_LIBDIR}/cmake/gstaichi
      )

  # Generate the config version file.
  set(GSTAICHI_VERSION "${TI_VERSION_MAJOR}.${TI_VERSION_MINOR}.${TI_VERSION_PATCH}")
  write_basic_package_version_file(
      "GsTaichiConfigVersion.cmake"
      VERSION ${GSTAICHI_VERSION}
      COMPATIBILITY SameMajorVersion
      )

  # Install the config files
  install(
      FILES
          "${CMAKE_CURRENT_BINARY_DIR}/GsTaichiConfig.cmake"
          "${CMAKE_CURRENT_BINARY_DIR}/GsTaichiConfigVersion.cmake"
      DESTINATION
          ${GSTAICHI_C_API_INSTALL_DIR}/gstaichi/${CMAKE_INSTALL_LIBDIR}/cmake/gstaichi
      )

  if(TI_WITH_LLVM)
  # Install runtime .bc files for LLVM backend
  install(DIRECTORY
        ${INSTALL_LIB_DIR}/runtime
        DESTINATION ${GSTAICHI_C_API_INSTALL_DIR})
  endif()

  # (penguinliong) Recover the original value in case it's used by other
  # targets.
  set(CMAKE_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX_BACKUP})
endfunction()

if (TI_WITH_PYTHON)
  install_gstaichi_c_api(PyGsTaichi python/gstaichi/_lib/c_api)
else()
  install_gstaichi_c_api(Distribute c_api)
endif()

if(TI_WITH_STATIC_C_API)
    # Traditional C++ static library is simply an archive of various .o files, resulting in a huge
    # file mixed with thousands of resolved or unresolved symbols.
    #
    # The key to a minimal static-library is to ask the static library to go through a relocation process,
    # which is only supported by the `ld` linker on Apple platform. The corresponding process is called `pre-link`:
    # https://stackoverflow.com/questions/14259405/pre-link-static-libraries-for-ios-project
    #
    # Here, we perform this `pre-link` on the compiled object files.

    # *** This gstaichi_static_c_api is NOT an executable ***
    # We faked an executable target because cmake does not have intrinsic support for pre-linked library targets
    add_executable(gstaichi_static_c_api ${C_API_SOURCE})
    set_target_properties(gstaichi_static_c_api PROPERTIES ENABLE_EXPORTS ON)

    get_target_property(GSTAICHI_C_API_INCLUDE_DIRS ${GSTAICHI_C_API_NAME} INCLUDE_DIRECTORIES)
    target_include_directories(gstaichi_static_c_api PRIVATE "${GSTAICHI_C_API_INCLUDE_DIRS}")

    target_link_libraries(gstaichi_static_c_api PRIVATE gstaichi_core_static)

    set(STATIC_LIB_LINK_OPTIONS "-Wl,-r")
    set(STATIC_LIB_LINK_OPTIONS "${STATIC_LIB_LINK_OPTIONS}" -Wl,-x)
    set(STATIC_LIB_LINK_OPTIONS "${STATIC_LIB_LINK_OPTIONS}" -Wl,-S)
    set(STATIC_LIB_LINK_OPTIONS "${STATIC_LIB_LINK_OPTIONS}" -Wl,-exported_symbols_list,${CMAKE_CURRENT_SOURCE_DIR}/c_api/version_scripts/export_symbols_mac.lds)
    target_link_options(gstaichi_static_c_api PRIVATE "${STATIC_LIB_LINK_OPTIONS}")
endif()
