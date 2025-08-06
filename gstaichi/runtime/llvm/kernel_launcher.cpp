#include "gstaichi/runtime/llvm/kernel_launcher.h"
#include <chrono>

namespace gstaichi::lang {
namespace LLVM {

KernelLauncher::KernelLauncher(Config config) : config_(std::move(config)) {
}

void KernelLauncher::launch_kernel(
    const lang::CompiledKernelData &compiled_kernel_data,
    LaunchContextBuilder &ctx) {
  TI_ASSERT(arch_uses_llvm(compiled_kernel_data.arch()));
  const auto &llvm_ckd =
      dynamic_cast<const LLVM::CompiledKernelData &>(compiled_kernel_data);
  auto start = std::chrono::high_resolution_clock::now();
  auto handle = register_llvm_kernel(llvm_ckd);
  auto end = std::chrono::high_resolution_clock::now();
  auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
  std::cout << "Registering LLVM kernel took {} microseconds" << duration.count() << std::endl;
  start = std::chrono::high_resolution_clock::now();
  launch_llvm_kernel(handle, ctx);
  end = std::chrono::high_resolution_clock::now();
  duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
  std::cout << "Launching LLVM kernel took {} microseconds " << duration.count() << std::endl;
}

}  // namespace LLVM
}  // namespace gstaichi::lang
