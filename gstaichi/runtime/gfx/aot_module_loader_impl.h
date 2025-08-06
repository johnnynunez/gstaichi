#pragma once

#include <any>
#include <string>
#include <vector>

#include "gstaichi/runtime/gfx/aot_utils.h"
#include "gstaichi/runtime/gfx/runtime.h"
#include "gstaichi/runtime/gfx/aot_module_builder_impl.h"
#include "gstaichi/runtime/gfx/aot_graph_data.h"
#include "gstaichi/codegen/spirv/kernel_utils.h"
#include "gstaichi/aot/module_builder.h"
#include "gstaichi/aot/module_loader.h"
#include "gstaichi/common/virtual_dir.h"

namespace gstaichi::lang {
namespace gfx {

struct TI_DLL_EXPORT AotModuleParams {
  std::string module_path{};
  const io::VirtualDir *dir{nullptr};
  GfxRuntime *runtime{nullptr};

  AotModuleParams() = default;

  [[deprecated]] AotModuleParams(const std::string &path, GfxRuntime *rt)
      : module_path(path), runtime(rt) {
  }
  AotModuleParams(const io::VirtualDir *dir, GfxRuntime *rt)
      : dir(dir), runtime(rt) {
  }
};

TI_DLL_EXPORT std::unique_ptr<aot::Module> make_aot_module(
    std::any mod_params,
    Arch device_api_backend);

}  // namespace gfx
}  // namespace gstaichi::lang
