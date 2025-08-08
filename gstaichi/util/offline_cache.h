#pragma once

#include <ctime>
#include <cstdint>
#include <queue>
#include <string>
#include <type_traits>
#include <unordered_map>

#include "gstaichi/common/core.h"
#include "gstaichi/common/cleanup.h"
#include "gstaichi/common/version.h"
#include "gstaichi/rhi/arch.h"
#include "gstaichi/util/io.h"
#include "gstaichi/util/lock.h"
#include "gstaichi/program/compile_config.h"

namespace gstaichi::lang {
namespace offline_cache {

// constexpr char kSpirvCacheFilenameExt[] = "spv";
// constexpr char kMetalCacheFilenameExt[] = "metal";
// constexpr char kLlvmCachSubPath[] = "llvm";
// constexpr char kSpirvCacheSubPath[] = "gfx";
// constexpr char kMetalCacheSubPath[] = "metal";

using Version = std::uint16_t[3];  // {MAJOR, MINOR, PATCH}

template <typename KernelMetadataType>
struct Metadata {
  using KernelMetadata = KernelMetadataType;

  Version version{};
  std::size_t size{0};  // byte
  std::unordered_map<std::string, KernelMetadata> kernels;

  // NOTE: The "version" must be the first field to be serialized
  TI_IO_DEF(version, size, kernels);
};

enum class LoadMetadataError {
  kNoError,
  kCorrupted,
  kFileNotFound,
  kVersionNotMatched,
};

template <typename MetadataType>
inline LoadMetadataError load_metadata_with_checking(
    MetadataType &result,
    const std::string &filepath) {
  if (!gstaichi::path_exists(filepath)) {
    TI_DEBUG("Offline cache metadata file {} not found", filepath);
    return LoadMetadataError::kFileNotFound;
  }

  using VerType = std::remove_reference_t<decltype(result.version)>;
  static_assert(std::is_same_v<VerType, Version>);
  const std::vector<uint8> bytes = read_data_from_file(filepath);

  VerType ver{};
  if (!read_from_binary(ver, bytes.data(), bytes.size(), false)) {
    return LoadMetadataError::kCorrupted;
  }
  if (ver[0] != TI_VERSION_MAJOR || ver[1] != TI_VERSION_MINOR ||
      ver[2] != TI_VERSION_PATCH) {
    TI_DEBUG("The offline cache metadata file {} is old (version={}.{}.{})",
             filepath, ver[0], ver[1], ver[2]);
    return LoadMetadataError::kVersionNotMatched;
  }

  return !read_from_binary(result, bytes.data(), bytes.size())
             ? LoadMetadataError::kCorrupted
             : LoadMetadataError::kNoError;
}

template <typename CacheDataType>
class FileCache {
public:
  using CacheData = CacheDataType;
  using CacheMetadata = Metadata<CacheData>;
  
  struct Config {
    std::string cache_subpath;           // e.g., "ptx"
    std::string file_extension;         // e.g., "ptx"
    std::string metadata_filename;      // e.g., "metadata.tcb"
    std::string metadata_lock_name;     // e.g., "metadata.lock"
    Arch arch;                          // for directory structure
    const CompileConfig &compile_config;
  };

  explicit FileCache(const Config &config) : config_(config) {
    if (config_.compile_config.offline_cache) {
      load_metadata();
    }
  }

  ~FileCache() {
    if (config_.compile_config.offline_cache) {
      save_metadata();
    }
  }

  // Try to load cached data
  bool load(const std::string &cache_key, std::string &content) {
    if (!config_.compile_config.offline_cache) {
      return false;
    }
    
    std::string filename = get_cache_filename(cache_key);
    if (load_file(filename, content)) {
      // Update last used time
      auto &kernels = cached_data_.kernels;
      auto iter = kernels.find(cache_key);
      if (iter != kernels.end()) {
        iter->second.last_used_at = std::time(nullptr);
      }
      return true;
    }
    return false;
  }

  // Save data to cache
  void save(const std::string &cache_key, const std::string &content) {
    if (!config_.compile_config.offline_cache) {
      return;
    }
    
    std::string filename = get_cache_filename(cache_key);
    if (save_file(filename, content)) {
      // Update metadata
      CacheData cache_data;
      cache_data.cache_key = cache_key;
      cache_data.size = content.size();
      cache_data.created_at = std::time(nullptr);
      cache_data.last_used_at = cache_data.created_at;
      
      cached_data_.kernels[cache_key] = cache_data;
      cached_data_.size += cache_data.size;
    }
  }

  // // Clean cache using existing infrastructure
  // void clean_cache() {
  //   if (!config_.compile_config.offline_cache) {
  //     return;
  //   }
    
  //   using CacheCleaner = CacheCleaner<CacheMetadata>;
  //   CacheCleanerConfig cleaner_config;
  //   cleaner_config.path = get_cache_path();
  //   cleaner_config.policy = string_to_clean_cache_policy(
  //       config_.compile_config.offline_cache_cleaning_policy);
  //   cleaner_config.cleaning_factor = config_.compile_config.offline_cache_cleaning_factor;
  //   cleaner_config.max_size = config_.compile_config.offline_cache_max_size_of_files;
  //   cleaner_config.metadata_filename = config_.metadata_filename;
  //   cleaner_config.debugging_metadata_filename = "metadata_debug.json";
  //   cleaner_config.metadata_lock_name = config_.metadata_lock_name;
    
  //   CacheCleaner::run(cleaner_config);
  // }

private:
  const Config config_;
  CacheMetadata cached_data_;

  std::string get_cache_path() {
    auto base_path = get_cache_path_by_arch(
        config_.compile_config.offline_cache_file_path, config_.arch);
    return join_path(base_path, config_.cache_subpath);
  }

  std::string get_cache_filename(const std::string &cache_key) {
    return join_path(get_cache_path(), cache_key + "." + config_.file_extension);
  }

  void load_metadata() {
    std::string cache_path = get_cache_path();
    std::string metadata_file = join_path(cache_path, config_.metadata_filename);
    std::string lock_file = join_path(cache_path, config_.metadata_lock_name);
    
    if (path_exists(metadata_file)) {
      if (lock_with_file(lock_file)) {
        auto _ = make_unlocker(lock_file);
        load_metadata_with_checking(cached_data_, metadata_file);
      }
    }
  }

  void save_metadata() {
    std::string cache_path = get_cache_path();
    std::string metadata_file = join_path(cache_path, config_.metadata_filename);
    std::string lock_file = join_path(cache_path, config_.metadata_lock_name);
    
    create_directories(cache_path);
    
    if (lock_with_file(lock_file)) {
      auto _ = make_unlocker(lock_file);
      
      cached_data_.version[0] = TI_VERSION_MAJOR;
      cached_data_.version[1] = TI_VERSION_MINOR;
      cached_data_.version[2] = TI_VERSION_PATCH;
      
      write_to_binary_file(cached_data_, metadata_file);
    }
  }

  bool load_file(const std::string &filename, std::string &content) {
    std::ifstream file(filename, std::ios::in);
    if (!file.is_open()) {
      return false;
    }
    
    std::ostringstream buffer;
    buffer << file.rdbuf();
    content = buffer.str();
    file.close();
    
    return true;
  }

  bool save_file(const std::string &filename, const std::string &content) {
    create_directories(get_cache_path());
    
    std::ofstream file(filename, std::ios::out);
    if (!file.is_open()) {
      return false;
    }
    
    file << content;
    file.close();
    
    return true;
  }
};

// Generic cache data structure for simple file caches
struct SimpleCacheData {
  std::string cache_key;
  std::size_t size{0};           // file size in bytes
  std::time_t created_at{0};     // for FIFO cleaning
  std::time_t last_used_at{0};   // for LRU cleaning

  TI_IO_DEF(cache_key, size, created_at, last_used_at);
};

// Generic cache cleaner utils for simple file caches
template <typename MetadataType>
struct SimpleCacheCleanerUtils {
  using KernelMetaData = typename MetadataType::KernelMetadata;
  
  static bool save_metadata(const CacheCleanerConfig &config,
                           const MetadataType &data) {
    auto filepath = join_path(config.path, config.metadata_filename);
    return write_to_binary_file(data, filepath);
  }

  static bool save_debugging_metadata(const CacheCleanerConfig &config,
                                     const MetadataType &data) {
    if (config.debugging_metadata_filename.empty()) {
      return true;
    }
    auto filepath = join_path(config.path, config.debugging_metadata_filename);
    TextSerializer ts;
    ts.serialize_to_json("cache", data);
    ts.write_to_file(filepath);
    return true;
  }

  static std::vector<std::string> get_cache_files(
      const CacheCleanerConfig &config,
      const KernelMetaData &kernel_meta) {
    // Extract file extension from one of the cache files
    std::string ext;
    if (auto pos = config.metadata_filename.find_last_of('.'); pos != std::string::npos) {
      // Assume cache files have a different extension than metadata
      ext = "ptx"; // This could be made configurable
    }
    return {kernel_meta.cache_key + "." + ext};
  }

  static void remove_other_files(const CacheCleanerConfig &config) {
  }

  static bool is_valid_cache_file(const CacheCleanerConfig &config,
                                 const std::string &name) {
    return true;
  }
};


void disable_offline_cache_if_needed(CompileConfig *config);
// std::string get_cache_path_by_arch(const std::string &base_path, Arch arch);
std::string mangle_name(const std::string &primal_name, const std::string &key);
bool try_demangle_name(const std::string &mangled_name,
                       std::string &primal_name,
                       std::string &key);

// // utils to manage the offline cache files
// std::size_t clean_offline_cache_files(const std::string &path);

}  // namespace offline_cache
}  // namespace gstaichi::lang
