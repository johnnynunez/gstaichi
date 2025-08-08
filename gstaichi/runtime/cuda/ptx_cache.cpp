// This was copy and hacked from kernel_compilation_manager.cpp
// It is used to manage the compilation and caching of PTX kernels

#include "picosha2.h"

#include "gstaichi/analysis/offline_cache_util.h"
#include "gstaichi/codegen/compiled_kernel_data.h"
#include "gstaichi/util/offline_cache.h"
#include "gstaichi/util/environ_config.h"

#include "gstaichi/runtime/cuda/ptx_cache.h"

namespace gstaichi::lang {

namespace offline_cache {

constexpr char kPtxCacheFilenameExt[] = "ptx";

template <>
struct CacheCleanerUtils<PtxCacheAllData> {
  using MetadataType = PtxCacheAllData;
  using KernelMetaData = typename MetadataType::WrappedData;

  // To save metadata as file
  static bool save_metadata(const CacheCleanerConfig &config,
                            const MetadataType &data) {
    write_to_binary_file(
        data, gstaichi::join_path(config.path, config.metadata_filename));
    return true;
  }

  static bool save_debugging_metadata(const CacheCleanerConfig &config,
                                      const MetadataType &data) {
    return true;
  }

  // To get cache files name
  static std::vector<std::string> get_cache_files(
      const CacheCleanerConfig &config,
      const KernelMetaData &kernel_meta) {
    auto fn = fmt::format(PtxCache::kCacheFilenameFormat,
                          kernel_meta.kernel_key);
    return {fn};
  }

  // To remove other files except cache files and offline cache metadta files
  static void remove_other_files(const CacheCleanerConfig &config) {
    // Do nothing
  }

  // To check if a file is cache file
  static bool is_valid_cache_file(const CacheCleanerConfig &config,
                                  const std::string &name) {
    std::string ext = filename_extension(name);
    return ext == kPtxCacheFilenameExt;
  }
};

}  // namespace offline_cache

PtxCache::PtxCache(Config config)
    : config_(std::move(config)),
    cache_dir_(join_path(config_.offline_cache_path, "ptx_cache"))
  {
  // this->cache_dir_ = join_path(config_.offline_cache_path, "kernel_compilation_manager");
  TI_DEBUG("Create ptxcache with offline_cache_file_path = {}",
           this->cache_dir_);
  auto filepath = join_path(this->cache_dir_, kMetadataFilename);
  auto lock_path = join_path(this->cache_dir_, kMetadataLockName);
  if (path_exists(filepath)) {
    if (lock_with_file(lock_path)) {
      auto _ = make_unlocker(lock_path);
      offline_cache::load_metadata_with_checking(cached_all_data_, filepath);
    } else {
      TI_WARN(
          "Lock {} failed. Please run 'ti cache clean -p {}' and try again.",
          lock_path, this->cache_dir_);
    }
  }
}

void PtxCache::dump() {
  if (wrapped_by_key_.empty()) {
    return;
  }

  TI_DEBUG("Dumping {} cached kernels to disk", wrapped_by_key_.size());

  gstaichi::create_directories(cache_dir_);
  auto filepath = join_path(cache_dir_, kMetadataFilename);
  auto lock_path = join_path(cache_dir_, kMetadataLockName);

  if (!lock_with_file(lock_path)) {
    TI_WARN("Lock {} failed. Please run 'ti cache clean -p {}' and try again.",
            lock_path, cache_dir_);
    wrapped_by_key_.clear();  // Ignore the caching kernels
    return;
  }

  auto _ = make_unlocker(lock_path);
  PtxCacheAllData data;
  data.version[0] = TI_VERSION_MAJOR;
  data.version[1] = TI_VERSION_MINOR;
  data.version[2] = TI_VERSION_PATCH;
  auto &wrappedDataByKey = data.wrappedDataByKey;
  // Load old cached data
  offline_cache::load_metadata_with_checking(data, filepath);
  // Update the cached data
  for (const auto *e : updated_data_) {
    auto iter = wrappedDataByKey.find(e->cache_key);
    if (iter != wrappedDataByKey.end()) {
      iter->second.last_used_at = e->last_used_at;
    }
  }
  // Add new data
  for (auto &[kernel_key, wrapped] : wrapped_by_key_) {
    if (wrapped.cache_mode == PtxCacheAllData::MemAndDiskCache) {
      auto [iter, ok] = wrappedDataByKey.insert({kernel_key, std::move(wrapped)});
      TI_ASSERT(!ok || iter->second.size == 0);
    }
  }
  // Clear caching_kernels_
  wrapped_by_key_.clear();
  // Dump cached CompiledKernelData to disk
  for (auto &[_, k] : wrappedDataByKey) {
    if (k.ptx) {
      auto cache_filename = make_filename(k.cache_key);
      std::ofstream fs{cache_filename, std::ios::out | std::ios::binary};
      TI_ASSERT(fs.is_open());
      fs << *(k.ptx);
      // auto err = k.ptx->dump(fs);
      // if (err == CompiledKernelData::Err::kNoError) {
        TI_ASSERT(!!fs);
        k.size = fs.tellp();
        data.size += k.size;
      // } else {
      //   TI_DEBUG("Dump cached CompiledKernelData(kernel_key={}) failed: {}",
      //            k.kernel_key, CompiledKernelData::get_err_msg(err));
      // }
    }
  }
  // Dump offline cache metadata
  if (!wrappedDataByKey.empty()) {
    write_to_binary_file(data, filepath);
  }
}

void PtxCache::clean_offline_cache(
    offline_cache::CleanCachePolicy policy,
    int max_bytes,
    double cleaning_factor) const {
  using CacheCleaner = offline_cache::CacheCleaner<PtxCacheAllData>;
  offline_cache::CacheCleanerConfig config;
  config.path = cache_dir_;
  config.policy = policy;
  config.cleaning_factor = cleaning_factor;
  config.max_size = max_bytes;
  config.metadata_filename = kMetadataFilename;
  config.debugging_metadata_filename = "";
  config.metadata_lock_name = kMetadataLockName;
  CacheCleaner::run(config);
}

std::string PtxCache::make_filename(
    const std::string &kernel_key) const {
  return join_path(cache_dir_,
                   fmt::format(kCacheFilenameFormat, kernel_key));
}

std::string PtxCache::make_cache_key(
    const CompileConfig &compile_config,
    const std::string &llvm_ir) const {
  picosha2::hash256_one_by_one hasher;
  std::string fast_math_str = compile_config.fast_math ? "1" : "0";
  hasher.process(fast_math_str.begin(), fast_math_str.end());
  hasher.process(llvm_ir.begin(), llvm_ir.end());
  hasher.finish();

  auto res = picosha2::get_hash_hex_string(hasher);
  res.insert(res.begin(), 'T');  // The key must start with a letter
  return res;
}

const CompiledKernelData *PtxCache::try_load_cached(
    const std::string &cache_key,
    CacheData::CacheMode cache_mode) {
  {  // Find in memory-cache (caching_kernels_)
    const auto &kernels = wrapped_by_key_;
    auto iter = kernels.find(cache_key);
    if (iter != kernels.end()) {
        std::cout << "found in memory cache "
                  << " key " << std::endl;
      return iter->second.compiled_kernel_data.get();
    }
  }
  // Find in disk-cache (cached_data_)
  if (cache_mode == CacheData::MemAndDiskCache) {
    auto &kernels = cached_data_.kernels;
    auto iter = kernels.find(kernel_key);
    if (iter != kernels.end()) {
      auto &k = iter->second;
      if (k.compiled_kernel_data) {
        TI_DEBUG("Create kernel '{}' from cache (key='{}')",
                 kernel_name, kernel_key);
        std::cout << "found ir kernel in cache as ckd " << kernel_name
                  << " key " << std::endl;
        return k.compiled_kernel_data.get();
      } else if (auto loaded = load_ckd(kernel_key, arch)) {
        TI_DEBUG("Create kernel '{}' from cache (key='{}')",
                 kernel_name, kernel_key);
        TI_ASSERT(loaded->arch() == arch);
        k.last_used_at = std::time(nullptr);
        k.compiled_kernel_data = std::move(loaded);
        updated_data_.push_back(&k);
        std::cout << "found ir kernel in cache maybe not sure " << kernel_name
                  << " key " << std::endl;
        return k.compiled_kernel_data.get();
      }
    }
  }
  return nullptr;
}

const CompiledKernelData &PtxCache::compile_and_cache_kernel(
    const std::string &kernel_key,
    const CompileConfig &compile_config,
    const DeviceCapabilityConfig &caps,
    const Kernel &kernel_def) {
  auto cache_mode = get_cache_mode(compile_config, kernel_def.ir_is_ast());
  TI_DEBUG_IF(cache_mode == CacheData::MemAndDiskCache,
              "Cache kernel '{}' (key='{}')", kernel_def.get_name(),
              kernel_key);
  TI_ASSERT(caching_kernels_.find(kernel_key) == caching_kernels_.end());
  KernelCacheData k;
  k.kernel_key = kernel_key;
  k.created_at = k.last_used_at = std::time(nullptr);

  std::cout << "cpp kernel_compilation_manager: compilng kernel '" << kernel_def.get_name()
            << "' (key='" << kernel_key << "')" << std::endl;
  if (get_environ_config("TI_SHOW_COMPILING")) {
    std::cout << "Compiling kernel '" << kernel_def.get_name()
              << "' (key='" << kernel_key << "')" << std::endl;
    TI_INFO("Compiling kernel '{}'", kernel_def.get_name());
  }
  k.compiled_kernel_data = compile_kernel(compile_config, caps, kernel_def);
  k.size = 0;  // Populate `size` within the PtxCache::dump()
  k.cache_mode = cache_mode;
  const auto &kernel_data = (caching_kernels_[kernel_key] = std::move(k));
  return *kernel_data.compiled_kernel_data;
}

void PtxCache::store_ptx(
    const std::string &checksum,
    const std::string &ptx
) {
  TI_DEBUG("Store PTX for kernel '{}' (key='{}')", checksum, ptx);
  // std::cout << "store_ptx checksum " << checksum << " ptx " << ptx << std::endl;
  // TI_ASSERT(caching_kernels_.find(checksum) == caching_kernels_.end());
  KernelCacheData k;
  k.kernel_key = checksum;
  k.created_at = k.last_used_at = std::time(nullptr);
  // k.compiled_kernel_data = std::make_unique<CompiledKernelData>(ptx);
  // TODO
  k.size = 0;  // Populate `size` within the PtxCache::dump()
  k.cache_mode = CacheData::MemAndDiskCache;
  wrapped_by_key_[checksum] = std::move(k);
}

const CompiledKernelData *PtxCache::load_ptx(
      const std::string &llvm_ir,
      cosnt std::string &ptx,
      const CompileConfig &compile_config) {
  // auto iter = caching_kernels_.find(checksum);
  // return nullptr;
  auto cache_mode = get_cache_mode(compile_config);
  auto res = try_load_cached_kernel(kernel_name, checksum, compile_config.arch,
                                cache_mode);
  // std::cout << "try_load_cached_kernel " << kernel_name << " checksum" << checksum << " arch " << arch_name(compile_config.arch)
  //   << " cache mode " << cache_mode << " res " << res << std::endl;
  return res;
  // try_load_cached_kernel(kernel_name, checksum, compile_config.arch,
  //                               get_cache_mode(compile_config, true));
}

const std::string PtxCache::load_ckd(
    const std::string &kernel_key,
    Arch arch) {
  const auto filename = make_filename(kernel_key);
  if (std::ifstream ifs(filename, std::ios::in | std::ios::binary);
      ifs.is_open()) {
    CompiledKernelData::Err err;
    auto ckd = CompiledKernelData::load(ifs, &err);
    if (err != CompiledKernelData::Err::kNoError) {
      TI_DEBUG("Load cache file {} failed: {}", filename,
               CompiledKernelData::get_err_msg(err));
      return nullptr;
    }
    if (auto err = ckd->check(); err != CompiledKernelData::Err::kNoError) {
      TI_DEBUG("Check CompiledKernelData loaded from {} failed: {}", filename,
               CompiledKernelData::get_err_msg(err));
      return nullptr;
    }
    return ckd;
  }
  return nullptr;
}

PtxCacheAllData::CacheMode PtxCache::get_cache_mode(
    const CompileConfig &compile_config) {
  return PtxCacheAllData::MemAndDiskCache;
}

}  // namespace gstaichi::lang
