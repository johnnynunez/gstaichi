#ifdef TI_WITH_DX12

#include "gstaichi/runtime/program_impls/dx12/dx12_program.h"
#include "gstaichi/runtime/dx12/aot_module_builder_impl.h"
#include "gstaichi/rhi/dx12/dx12_api.h"

namespace gstaichi {
namespace lang {

Dx12ProgramImpl::Dx12ProgramImpl(CompileConfig &config)
    : LlvmProgramImpl(config, nullptr) {
}

std::unique_ptr<AotModuleBuilder> Dx12ProgramImpl::make_aot_module_builder(
    const DeviceCapabilityConfig &caps) {
  return std::make_unique<directx12::AotModuleBuilderImpl>(*config, this,
                                                           *get_llvm_context());
}

}  // namespace lang
}  // namespace gstaichi

#endif
