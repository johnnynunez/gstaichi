#include "gstaichi/runtime/cuda/ptx_cache.h"
#include "gstaichi/rhi/cuda/cuda_context.h"
#include "gstaichi/runtime/cuda/jit_cuda.h"
#include "picosha2.h"

namespace gstaichi::lang {

PtxCache::PtxCache(const CompileConfig &config) 
  : file_cache_({
      .cache_subpath = kPtxCacheSubPath,
      .file_extension = kPtxCacheFilenameExt,
      .metadata_filename = kPtxMetadataFilename,
      .metadata_lock_name = kPtxMetadataLockName,
      .arch = Arch::cuda,
      .compile_config = config
    }) {
}

bool PtxCache::load_ptx(const llvm::Module *module, int max_reg, std::string &ptx) {
  std::string cache_key = generate_cache_key(module, max_reg);
  if (file_cache_.load(cache_key, ptx)) {
    TI_TRACE("PTX cache hit: {}", cache_key.substr(0, 8));
    return true;
  }
  
  TI_TRACE("PTX cache miss: {}", cache_key.substr(0, 8));
  return false;
}

void PtxCache::save_ptx(const llvm::Module *module, int max_reg, const std::string &ptx) {
  std::string cache_key = generate_cache_key(module, max_reg);
  file_cache_.save(cache_key, ptx);
  TI_TRACE("PTX saved to cache: {}", cache_key.substr(0, 8));
}

std::string PtxCache::generate_cache_key(const llvm::Module *module, int max_reg) {
  std::string module_str;
  llvm::raw_string_ostream stream(module_str);
  module->print(stream, nullptr);
  stream.flush();
  
  std::string combined = module_str + std::to_string(max_reg);
  
  // Add relevant config that affects PTX generation
  combined += std::to_string(config_.fast_math);
  combined += CUDAContext::get_instance().get_mcpu();
  combined += cuda_mattrs();
  
  picosha2::hash256_one_by_one hasher;
  hasher.process(combined.begin(), combined.end());
  hasher.finish();
  
  auto hash = picosha2::get_hash_hex_string(hasher);
  hash.insert(hash.begin(), 'T'); // Ensure it starts with a letter
  return hash;
}

}  // namespace gstaichi::lang