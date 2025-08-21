#include "gstaichi/platform/cuda/detect_cuda.h"

#if defined(TI_WITH_CUDA)
#include "gstaichi/rhi/cuda/cuda_driver.h"
#endif

namespace gstaichi {

bool is_cuda_api_available() {
#if defined(TI_WITH_CUDA)
  try {
    auto &instance = lang::CUDADriver::get_instance_without_context();
    return instance.detected();
  } catch (const std::exception &e) {
    std::cerr << "Error occurred while checking CUDA availability: " << e.what()
              << std::endl;
    return false;
  } catch (...) {
    std::cerr << "Unknown error occurred while checking CUDA availability."
              << std::endl;
    return false;
  }
#else
  return false;
#endif
}

}  // namespace gstaichi
