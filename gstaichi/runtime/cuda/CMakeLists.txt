# ./gstaichi/runtime/cuda/CMakeLists.txt

add_library(cuda_runtime)
target_sources(cuda_runtime
  PRIVATE
    ptx_cache.cpp
    jit_cuda.cpp
    kernel_launcher.cpp
  )

target_include_directories(cuda_runtime
  PRIVATE
    ${PROJECT_SOURCE_DIR}
    ${PROJECT_SOURCE_DIR}/external/eigen
    ${PROJECT_SOURCE_DIR}/external/spdlog/include
    ${PROJECT_SOURCE_DIR}/external/PicoSHA2
    ${LLVM_INCLUDE_DIRS}
  )
