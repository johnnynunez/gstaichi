#pragma once

#include "gstaichi/codegen/llvm/compiled_kernel_data.h"
#include "gstaichi/runtime/llvm/kernel_launcher.h"

namespace gstaichi::lang {
namespace cpu {

class KernelLauncher : public LLVM::KernelLauncher {
  using Base = LLVM::KernelLauncher;

  struct Context {
    using TaskFunc = int32 (*)(void *);
    std::vector<TaskFunc> task_funcs;
    std::vector<std::pair<std::vector<int>, Callable::Parameter>> parameters;
  };

 public:
  using Base::Base;

  void launch_llvm_kernel(Handle handle, LaunchContextBuilder &ctx) override;
  Handle register_llvm_kernel(
      const LLVM::CompiledKernelData &compiled) override;

 private:
  std::vector<Context> contexts_;
};

}  // namespace cpu
}  // namespace gstaichi::lang
