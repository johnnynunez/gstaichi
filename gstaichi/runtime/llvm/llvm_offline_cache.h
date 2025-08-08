#pragma once

#include <memory>

#ifdef TI_WITH_LLVM
#include "llvm/IR/Module.h"
#include "gstaichi/common/core.h"
#include "gstaichi/common/serialization.h"
#include "gstaichi/program/kernel.h"
#include "gstaichi/util/offline_cache.h"
#include "gstaichi/codegen/llvm/llvm_compiled_data.h"
#include "gstaichi/codegen/llvm/compiled_kernel_data.h"

namespace gstaichi::lang {

// NOTE: The LlvmOfflineCache, LlvmOfflineCacheFileReader and
// LlvmOfflineCacheFileWriter are only used by LLVM AOT now.
// TODO(PGZXB): Rename these structs/classes.

struct LlvmOfflineCache {
  using Version = uint16[3];  // {MAJOR, MINOR, PATCH}

  enum Format {
    LL = 0x01,
    BC = 0x10,
  };

  struct KernelCacheData {
    std::string kernel_key;
    std::vector<std::pair<std::vector<int>, Callable::Parameter>> args;
    std::vector<Callable::Ret> rets;
    LLVMCompiledKernel compiled_data;

    const StructType *ret_type = nullptr;
    size_t ret_size{0};

    const StructType *args_type = nullptr;
    size_t args_size{0};

    // For cache cleaning
    std::size_t size{0};          // byte
    std::time_t created_at{0};    // millsec
    std::time_t last_used_at{0};  // millsec

    KernelCacheData() = default;
    KernelCacheData(KernelCacheData &&) = default;
    KernelCacheData &operator=(KernelCacheData &&) = default;
    ~KernelCacheData() = default;

    KernelCacheData clone() const;
    LLVM::CompiledKernelData::InternalData convert_to_llvm_ckd_data() const;

    TI_IO_DEF(kernel_key,
              args,
              compiled_data,
              size,
              created_at,
              last_used_at,
              rets,
              ret_type,
              ret_size,
              args_type,
              args_size);
  };

  struct FieldCacheData {
    struct SNodeCacheData {
      int id{0};
      SNodeType type = SNodeType::undefined;
      size_t cell_size_bytes{0};
      size_t chunk_size{0};

      TI_IO_DEF(id, type, cell_size_bytes, chunk_size);
    };

    int tree_id{0};
    int root_id{0};
    size_t root_size{0};
    std::vector<SNodeCacheData> snode_metas;

    TI_IO_DEF(tree_id, root_id, root_size, snode_metas);

    // TODO(zhanlue): refactor llvm::Modules
    //
    // struct_module will eventually get cloned into each kernel_module,
    // so there's no need to serialize it here.
    //
    // We have three different types of llvm::Module
    // 1. runtime_module: contains runtime functions.
    // 2. struct_module: contains compiled SNodeTree in llvm::Type.
    // 3. kernel_modules: contains compiled kernel codes.
    //
    // The way those modules work rely on a recursive clone mechanism:
    //   runtime_module = load("runtime.bc")
    //   struct_module = clone(runtime_module) + compiled-SNodeTree
    //   kernel_module = clone(struct_module) + compiled-Kernel
    //
    // As a result, every kernel_module contains a copy of struct_module +
    // runtime_module.
    //
    // This recursive clone mechanism is super fragile,
    // which potentially causes inconsistency between modules if not handled
    // properly.
    //
    // Let's turn to use llvm::link to bind the modules,
    // and make runtime_module, struct_module, kernel_module independent of each
    // other
  };

  using KernelMetadata = KernelCacheData;  // Required by CacheCleaner

  Version version{};
  std::size_t size{0};  // byte

  // TODO(zhanlue): we need a better identifier for each FieldCacheData
  // (SNodeTree) Given that snode_tree_id is not continuous, it is ridiculous to
  // ask the users to remember each of the snode_tree_ids
  // ** Find a way to name each SNodeTree **
  std::unordered_map<int, FieldCacheData> fields;  // key = snode_tree_id

  std::unordered_map<std::string, KernelCacheData>
      kernels;  // key = kernel_name

  // NOTE: The "version" must be the first field to be serialized
  TI_IO_DEF(version, size, fields, kernels);
};

}  // namespace gstaichi::lang
#endif  // TI_WITH_LLVM
