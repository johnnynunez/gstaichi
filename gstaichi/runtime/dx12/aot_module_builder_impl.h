#pragma once

#include "gstaichi/aot/module_builder.h"
#include "gstaichi/runtime/llvm/llvm_offline_cache.h"
#include "gstaichi/runtime/llvm/llvm_aot_module_builder.h"
#include "gstaichi/aot/module_data.h"

namespace gstaichi::lang {
namespace directx12 {

struct ModuleDataDX12 : public aot::ModuleData {
  std::unordered_map<std::string, std::vector<std::vector<uint8_t>>> dxil_codes;
};

class AotModuleBuilderImpl : public AotModuleBuilder {
 public:
  explicit AotModuleBuilderImpl(const CompileConfig &config,
                                LlvmProgramImpl *prog,
                                GsTaichiLLVMContext &tlctx);

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

  const CompileConfig &config_;
  LlvmProgramImpl *prog;
  ModuleDataDX12 module_data;
  GsTaichiLLVMContext &tlctx_;
};

}  // namespace directx12
}  // namespace gstaichi::lang
