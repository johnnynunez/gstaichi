#pragma once
#ifdef TI_WITH_LLVM

#include "gstaichi_core_impl.h"

#ifdef TI_WITH_CUDA
#include "gstaichi/platform/cuda/detect_cuda.h"
#endif

namespace gstaichi::lang {
class LlvmRuntimeExecutor;
struct CompileConfig;
}  // namespace gstaichi::lang

namespace capi {

class LlvmRuntime : public Runtime {
 public:
  LlvmRuntime(gstaichi::Arch arch);
  virtual ~LlvmRuntime();

  void check_runtime_error();
  gstaichi::lang::Device &get() override;

 private:
  /* Internally used interfaces */
  TiAotModule load_aot_module(const char *module_path) override;
  TiMemory allocate_memory(
      const gstaichi::lang::Device::AllocParams &params) override;
  void free_memory(TiMemory devmem) override;

  void buffer_copy(const gstaichi::lang::DevicePtr &dst,
                   const gstaichi::lang::DevicePtr &src,
                   size_t size) override;

  void flush() override;

  void wait() override;

 private:
  std::unique_ptr<gstaichi::lang::CompileConfig> cfg_{nullptr};
  std::unique_ptr<gstaichi::lang::LlvmRuntimeExecutor> executor_{nullptr};
  gstaichi::uint64 *result_buffer{nullptr};
};

}  // namespace capi

#endif  // TI_WITH_LLVM
