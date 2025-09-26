#pragma once

#include <ctime>
#include <string>
#include <memory>
#include <unordered_map>

#include "gstaichi/util/offline_cache.h"
#include "gstaichi/codegen/kernel_compiler.h"
#include "gstaichi/codegen/compiled_kernel_data.h"

namespace gstaichi::lang {

struct CacheData {
  enum CacheMode {
    MemCache,        // Cache the kernel in memory
    MemAndDiskCache  // Cache the kernel in memory and disk
  };
  using Version = std::uint16_t[3];

  struct Metadata {
    std::string kernel_key;
    std::size_t size{0};          // byte
    std::time_t created_at{0};    // sec
    std::time_t last_used_at{0};  // sec

    // Dump the kernel to disk if `cache_mode` == `MemAndDiskCache`
    CacheMode cache_mode{MemCache};
    TI_IO_DEF(kernel_key, size, created_at, last_used_at);
  };

  struct DataWrapper {
    Metadata metadata;
    std::unique_ptr<lang::CompiledKernelData> compiled_kernel_data;

    TI_IO_DEF(metadata);
  };

  Version version{};
  std::size_t size{0};
  std::unordered_map<std::string, DataWrapper> dataWrapperByCacheKey;

  // NOTE: The "version" must be the first field to be serialized
  TI_IO_DEF(version, size, dataWrapperByCacheKey);
};

struct CompileResult {
  const CompiledKernelData &compiled_kernel_data;
  bool cache_hit;
  std::string cache_key;
};

class KernelCompilationManager final {
 public:
  static constexpr char kMetadataFilename[] = "ticache.tcb";
  static constexpr char kCacheFilenameFormat[] = "{}.tic";
  static constexpr char kMetadataLockName[] = "ticache.lock";

  using KernelCacheData = CacheData::DataWrapper;
  using CachingKernels = std::unordered_map<std::string, KernelCacheData>;

  struct Config {
    std::string offline_cache_path;
    std::unique_ptr<KernelCompiler> kernel_compiler;
  };

  explicit KernelCompilationManager(Config init_params);

  // Load from memory || Load from disk || (Compile && Cache in memory)
  CompileResult load_or_compile(const CompileConfig &compile_config,
                                const DeviceCapabilityConfig &caps,
                                const Kernel &kernel_def);

  // Dump the cached data in memory to disk
  void dump();

  // Run offline cache cleaning
  void clean_offline_cache(offline_cache::CleanCachePolicy policy,
                           int max_bytes,
                           double cleaning_factor) const;

  void store_fast_cache(const std::string &checksum,
                        const Kernel &kernel,
                        const CompileConfig &compile_config,
                        const DeviceCapabilityConfig &caps,
                        CompiledKernelData &ckd);

  const CompiledKernelData *load_fast_cache(const std::string &checksum,
                                            const std::string &kernel_name,
                                            const CompileConfig &compile_config,
                                            const DeviceCapabilityConfig &caps);

 private:
  std::string make_filename(const std::string &kernel_key) const;

  std::unique_ptr<CompiledKernelData> compile_kernel(
      const CompileConfig &compile_config,
      const DeviceCapabilityConfig &caps,
      const Kernel &kernel_def) const;

  std::string make_kernel_key(const CompileConfig &compile_config,
                              const DeviceCapabilityConfig &caps,
                              const Kernel &kernel_def) const;

  const CompiledKernelData *try_load_cached_kernel(
      const std::string &kernel_name,
      const std::string &kernel_key,
      Arch arch,
      CacheData::CacheMode cache_mode);

  const CompiledKernelData &compile_and_cache_kernel(
      const std::string &kernel_key,
      const CompileConfig &compile_config,
      const DeviceCapabilityConfig &caps,
      const Kernel &kernel_def);

  std::unique_ptr<CompiledKernelData> load_ckd(const std::string &kernel_key,
                                               Arch arch);

  static CacheData::CacheMode get_cache_mode(
      const CompileConfig &compile_config,
      bool kernel_ir_is_ast);

  Config config_;
  CachingKernels caching_kernels_;
  CacheData cached_data_;
  std::vector<KernelCacheData *> updated_data_;
  const std::string cache_dir_;
};

}  // namespace gstaichi::lang
