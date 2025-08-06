#include "gstaichi/platform/amdgpu/detect_amdgpu.h"

#if defined(TI_WITH_AMDGPU)
#include "gstaichi/rhi/amdgpu/amdgpu_driver.h"
#endif

namespace gstaichi {

bool is_rocm_api_available() {
#if defined(TI_WITH_AMDGPU)
  return lang::AMDGPUDriver::get_instance_without_context().detected();
#else
  return false;
#endif
}

}  // namespace gstaichi
