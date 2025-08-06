#pragma once

#include <any>
#include <string>
#include <vector>

#include "gstaichi/aot/module_builder.h"
#include "gstaichi/aot/module_loader.h"

namespace gstaichi {
namespace lang {
namespace directx12 {

struct TI_DLL_EXPORT AotModuleParams {
  std::string module_path;
};

TI_DLL_EXPORT std::unique_ptr<aot::Module> make_aot_module(
    std::any mod_params,
    Arch device_api_backend);

}  // namespace directx12
}  // namespace lang
}  // namespace gstaichi
