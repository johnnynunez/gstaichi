#pragma once

#include "gstaichi/codegen/compiled_kernel_data.h"
#include "gstaichi/program/launch_context_builder.h"
// #include "gstaichi/program/program_impl.h"

namespace gstaichi::lang {

class ProgramImpl;

class KernelLauncher {
 public:
  using Handle = KernelLaunchHandle;

  KernelLauncher(const ProgramImpl *program_impl)
      : program_impl_(program_impl) {
  }
  virtual void launch_kernel(const CompiledKernelData &compiled_kernel_data,
                             LaunchContextBuilder &ctx) = 0;

  virtual ~KernelLauncher() = default;

protected:
  const ProgramImpl *program_impl_;
};

}  // namespace gstaichi::lang
