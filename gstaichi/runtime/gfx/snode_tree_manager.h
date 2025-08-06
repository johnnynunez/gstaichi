#pragma once

#include <vector>

#include "gstaichi/rhi/device.h"
#include "gstaichi/codegen/spirv/snode_struct_compiler.h"
#include "gstaichi/struct/snode_tree.h"

namespace gstaichi::lang {
namespace gfx {

class GfxRuntime;

/**
 * @brief Manages the SNodeTrees for the underlying backend.
 *
 */
class SNodeTreeManager {
 private:
  using CompiledSNodeStructs = gstaichi::lang::spirv::CompiledSNodeStructs;

 public:
  explicit SNodeTreeManager(GfxRuntime *rtm);

  const std::vector<CompiledSNodeStructs> &get_compiled_structs() const {
    return compiled_snode_structs_;
  }

  void materialize_snode_tree(SNodeTree *tree);

  void destroy_snode_tree(SNodeTree *snode_tree);

  size_t get_field_in_tree_offset(int tree_id, const SNode *child);

  DevicePtr get_snode_tree_device_ptr(int tree_id);

 private:
  GfxRuntime *const runtime_;
  std::vector<CompiledSNodeStructs> compiled_snode_structs_;
};

}  // namespace gfx
}  // namespace gstaichi::lang
