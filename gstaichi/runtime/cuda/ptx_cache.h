// This was copy and hacked from kernel_compilation_manager.h
// It is used to manage the compilation and caching of PTX kernels
#pragma once

#include <ctime>
#include <string>
#include <memory>
#include <unordered_map>

#include "gstaichi/util/offline_cache.h"

namespace gstaichi::lang {

struct PtxCacheAllData {
  enum CacheMode {
    MemCache,        // Cache the kernel in memory
    MemAndDiskCache  // Cache the kernel in memory and disk
  };
  using Version = std::uint16_t[3];

  struct WrappedData {
    std::string cache_key;
    std::size_t size{0};          // byte
    std::time_t created_at{0};    // sec
    std::time_t last_used_at{0};  // sec

    // Dump the kernel to disk if `cache_mode` == `MemAndDiskCache`
    CacheMode cache_mode{MemCache};

    const std::string *ptx;

    TI_IO_DEF(cache_key, size, created_at, last_used_at);
  };

  // using KernelMetadata = Metadata;  // Required by CacheCleaner

  Version version{};
  std::size_t size{0};
  std::unordered_map<std::string, WrappedData> wrappedDataByKey;

  // NOTE: The "version" must be the first field to be serialized
  TI_IO_DEF(version, size, wrappedDataByKey);
};

class PtxCache final {
 public:
  static constexpr char kMetadataFilename[] = "ptxcache.tcb";
  static constexpr char kCacheFilenameFormat[] = "{}.ptx";
  static constexpr char kMetadataLockName[] = "ptxcache.lock";

  // using CacheData = PtxCacheData::Data;
  using WrappedByKey = std::unordered_map<std::string, PtxCacheAllData::WrappedData>;

  struct Config {
    std::string offline_cache_path;
  };

  explicit PtxCache(Config init_params);

  // Dump the cached data in memory to disk
  void dump();

  void clean_offline_cache(offline_cache::CleanCachePolicy policy,
                           int max_bytes,
                           double cleaning_factor) const;

  std::string make_cache_key(
    const CompileConfig &compile_config,
    const std::string &llvm_ir) const;

  void store_ptx(
    const std::string &checksum,
    const std::string &ptx
  );

  const std::string load_ptx(
      const std::string &llvm_ir,
      const std::string &ptx,
      const CompileConfig &compile_config);

 private:
  std::string make_filename(const std::string &kernel_key) const;
  static PtxCacheAllData::CacheMode get_cache_mode(
      const CompileConfig &compile_config
  );

  Config config_;
  using WrappedData = PtxCacheAllData::WrappedData;
  std::unordered_map<std::string, WrappedData> wrapped_by_key_;  // caching_kernels_ in kernel_compilation_manager
  PtxCacheAllData cached_all_data_;  // cached_data_ in kernel_compilation_manager
  std::vector<WrappedData *> updated_data_;
  const std::string cache_dir_;

  // kernel_compilation_manager:
  // using KernelCacheData = CacheData::WrappedData;
  // using CachingKernels = std::unordered_map<std::string, KernelCacheData>;

  // CachingKernels caching_kernels_;
  // CacheData cached_data_;
  // std::vector<KernelCacheData *> updated_data_;
};

}  // namespace gstaichi::lang
