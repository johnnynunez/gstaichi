#include "gstaichi/program/program_impl.h"
#include "gstaichi/runtime/llvm/kernel_launcher.h"

namespace gstaichi::lang {

namespace LLVM {

KernelLauncher::KernelLauncher(Config config, const ::gstaichi::lang::ProgramImpl *program_impl)
    : gstaichi::lang::KernelLauncher(program_impl), config_(std::move(config))
       {
}

void KernelLauncher::launch_kernel(
    const lang::CompiledKernelData &compiled_kernel_data,
    LaunchContextBuilder &ctx) {
  TI_ASSERT(arch_uses_llvm(compiled_kernel_data.arch()));
  const auto &llvm_ckd =
      dynamic_cast<const LLVM::CompiledKernelData &>(compiled_kernel_data);
  auto handle = register_llvm_kernel(llvm_ckd);
  launch_llvm_kernel(handle, ctx);
}

}  // namespace LLVM
}  // namespace gstaichi::lang
