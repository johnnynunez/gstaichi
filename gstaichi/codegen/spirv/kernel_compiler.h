#pragma once

#include <memory>

#include "gstaichi/codegen/kernel_compiler.h"
#include "gstaichi/codegen/compiled_kernel_data.h"
#include "gstaichi/codegen/spirv/snode_struct_compiler.h"

namespace gstaichi::lang {
namespace spirv {

class KernelCompiler : public lang::KernelCompiler {
 public:
  struct Config {
    // NOTE: Ideally, compiled_struct_data should be used as an argument to
    // KernelCompiler::compile, but this necessitates the use of a unified
    // structure to represent the compiled struct.
    const std::vector<CompiledSNodeStructs> *compiled_struct_data{nullptr};
  };

  explicit KernelCompiler(Config config);

  IRNodePtr compile(const CompileConfig &compile_config,
                    const Kernel &kernel_def) const override;

  CKDPtr compile(const CompileConfig &compile_config,
                 const DeviceCapabilityConfig &device_caps,
                 const Kernel &kernel_def,
                 IRNode &chi_ir) const override;

 private:
  Config config_;
};

}  // namespace spirv
}  // namespace gstaichi::lang
