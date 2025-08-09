#include "gfx_program.h"

#include "gstaichi/analysis/offline_cache_util.h"
#include "gstaichi/codegen/spirv/kernel_compiler.h"
#include "gstaichi/runtime/gfx/kernel_launcher.h"
#include "gstaichi/rhi/common/host_memory_pool.h"

namespace gstaichi::lang {

GfxProgramImpl::GfxProgramImpl(CompileConfig &config) : ProgramImpl(config) {
}

void GfxProgramImpl::compile_snode_tree_types(SNodeTree *tree) {
  if (runtime_) {
    snode_tree_mgr_->materialize_snode_tree(tree);
  } else {
    gfx::CompiledSNodeStructs compiled_structs =
        gfx::compile_snode_structs(*tree->root());
  }
}

void GfxProgramImpl::materialize_snode_tree(SNodeTree *tree,
                                            uint64 *result_buffer) {
  snode_tree_mgr_->materialize_snode_tree(tree);
}

DeviceAllocation GfxProgramImpl::allocate_memory_on_device(
    std::size_t alloc_size,
    uint64 *result_buffer) {
  DeviceAllocation alloc;
  RhiResult res = get_compute_device()->allocate_memory(
      {alloc_size, /*host_write=*/false, /*host_read=*/false,
       /*export_sharing=*/false},
      &alloc);
  TI_ASSERT(res == RhiResult::success);
  return alloc;
}

DeviceAllocation GfxProgramImpl::allocate_texture(const ImageParams &params) {
  return runtime_->create_image(params);
}

void GfxProgramImpl::finalize() {
  runtime_.reset();
  device_.reset();
}

GfxProgramImpl::~GfxProgramImpl() {
  // Calling virtual methods in destructors is unsafe. Use static-binding here.
  GfxProgramImpl::finalize();
}

std::unique_ptr<KernelCompiler> GfxProgramImpl::make_kernel_compiler() {
  spirv::KernelCompiler::Config cfg;
  cfg.compiled_struct_data = &snode_tree_mgr_->get_compiled_structs();
  return std::make_unique<spirv::KernelCompiler>(std::move(cfg));
}

std::unique_ptr<KernelLauncher> GfxProgramImpl::make_kernel_launcher() {
  gfx::KernelLauncher::Config cfg;
  cfg.gfx_runtime_ = runtime_.get();
  return std::make_unique<gfx::KernelLauncher>(std::move(cfg), this);
}

DeviceCapabilityConfig GfxProgramImpl::get_device_caps() {
  TI_ASSERT(runtime_);
  return runtime_->get_ti_device()->get_caps();
}

}  // namespace gstaichi::lang
