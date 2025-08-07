#pragma once

#include <memory>
#include <string>

#include "gstaichi/util/offline_cache.h"
#include "gstaichi/program/compile_config.h"
#include "llvm/IR/Module.h"

namespace gstaichi::lang {

constexpr char kPtxCacheFilenameExt[] = "ptx";
constexpr char kPtxCacheSubPath[] = "ptx";
constexpr char kPtxMetadataFilename[] = "metadata.tcb";
constexpr char kPtxMetadataLockName[] = "metadata.lock";

using PtxCacheData = offline_cache::SimpleCacheData;
using PtxCacheMetadata = offline_cache::Metadata<PtxCacheData>;

template <>
struct offline_cache::CacheCleanerUtils<PtxCacheMetadata> 
  : offline_cache::SimpleCacheCleanerUtils<PtxCacheMetadata> {
  
  static bool is_valid_cache_file(const offline_cache::CacheCleanerConfig &config,
                                 const std::string &name) {
    return filename_extension(name) == kPtxCacheFilenameExt;
  }

  static std::vector<std::string> get_cache_files(
      const offline_cache::CacheCleanerConfig &config,
      const KernelMetaData &kernel_meta) {
    return {kernel_meta.cache_key + "." + kPtxCacheFilenameExt};
  }
};

class PtxCache {
public:
  explicit PtxCache(const CompileConfig &config);
  
  bool load_ptx(const llvm::Module *module, int max_reg, std::string &ptx);  
  void save_ptx(const llvm::Module *module, int max_reg, const std::string &ptx);
  void clean_cache() { file_cache_.clean_cache(); }

private:
  offline_cache::FileCache<PtxCacheData> file_cache_;
  
  std::string generate_cache_key(const llvm::Module *module, int max_reg);
};

}  // namespace gstaichi::lang