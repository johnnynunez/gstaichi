#ifdef TI_WITH_DX11

#include "gstaichi/runtime/program_impls/dx/dx_program.h"

#include "gstaichi/rhi/dx/dx_api.h"
#include "gstaichi/codegen/spirv/kernel_compiler.h"
#include "gstaichi/codegen/spirv/compiled_kernel_data.h"
#include "gstaichi/runtime/gfx/snode_tree_manager.h"
#include "gstaichi/runtime/gfx/aot_module_builder_impl.h"
#include "gstaichi/runtime/gfx/kernel_launcher.h"
#include "gstaichi/codegen/spirv/spirv_codegen.h"
#include "gstaichi/rhi/common/host_memory_pool.h"

namespace gstaichi::lang {

Dx11ProgramImpl::Dx11ProgramImpl(CompileConfig &config)
    : GfxProgramImpl(config) {
}

void Dx11ProgramImpl::materialize_runtime(KernelProfilerBase *profiler,
                                          uint64 **result_buffer_ptr) {
  *result_buffer_ptr = (uint64 *)HostMemoryPool::get_instance().allocate(
      sizeof(uint64) * gstaichi_result_buffer_entries, 8);

  device_ = directx11::make_dx11_device();

  gfx::GfxRuntime::Params params;
  params.device = device_.get();
  runtime_ = std::make_unique<gfx::GfxRuntime>(std::move(params));
  snode_tree_mgr_ = std::make_unique<gfx::SNodeTreeManager>(runtime_.get());
}

}  // namespace gstaichi::lang

#endif
