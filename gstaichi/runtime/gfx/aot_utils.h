#pragma once

#include <vector>
#include <map>

#include "gstaichi/codegen/spirv/kernel_utils.h"
#include "gstaichi/aot/module_loader.h"

namespace gstaichi::lang {
namespace gfx {

/**
 * AOT module data for the Unified Device API backend.
 */
struct GsTaichiAotData {
  //   BufferMetaData metadata;
  std::vector<std::vector<std::vector<uint32_t>>> spirv_codes;
  std::vector<spirv::GsTaichiKernelAttributes> kernels;
  std::vector<aot::CompiledFieldData> fields;
  std::map<std::string, uint32_t> required_caps;
  size_t root_buffer_size{0};

  TI_IO_DEF(kernels, fields, required_caps, root_buffer_size);
};

}  // namespace gfx
}  // namespace gstaichi::lang
