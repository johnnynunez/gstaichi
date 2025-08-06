#pragma once

#include <string>
#include <vector>

#include "gstaichi/aot/module_builder.h"
#include "gstaichi/runtime/gfx/aot_utils.h"
#include "gstaichi/codegen/spirv/snode_struct_compiler.h"
#include "gstaichi/codegen/spirv/kernel_utils.h"
#include "gstaichi/compilation_manager/kernel_compilation_manager.h"

namespace gstaichi::lang {
namespace gfx {

class AotModuleBuilderImpl : public AotModuleBuilder {
 public:
  explicit AotModuleBuilderImpl(
      const std::vector<spirv::CompiledSNodeStructs> &compiled_structs,
      KernelCompilationManager &compilation_manager,
      const CompileConfig &compile_config,
      const DeviceCapabilityConfig &caps);

  void dump(const std::string &output_dir,
            const std::string &filename) const override;

 private:
  void add_per_backend(const std::string &identifier, Kernel *kernel) override;

  void add_field_per_backend(const std::string &identifier,
                             const SNode *rep_snode,
                             bool is_scalar,
                             DataType dt,
                             std::vector<int> shape,
                             int row_num,
                             int column_num) override;

  void add_per_backend_tmpl(const std::string &identifier,
                            const std::string &key,
                            Kernel *kernel) override;

  std::string write_spv_file(const std::string &output_dir,
                             const spirv::TaskAttributes &k,
                             const std::vector<uint32_t> &source_code) const;

  const std::vector<spirv::CompiledSNodeStructs> &compiled_structs_;
  GsTaichiAotData ti_aot_data_;

  KernelCompilationManager &compilation_manager_;
  const CompileConfig &config_;
  DeviceCapabilityConfig caps_;
};

}  // namespace gfx
}  // namespace gstaichi::lang
