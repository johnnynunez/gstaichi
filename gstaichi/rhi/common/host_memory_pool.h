#pragma once
#include "gstaichi/common/core.h"
#include "gstaichi/rhi/common/unified_allocator.h"
#include "gstaichi/rhi/device.h"
#include <mutex>
#include <vector>
#include <memory>
#include <thread>

namespace gstaichi::lang {

// A memory pool that runs on the host

class TI_DLL_EXPORT HostMemoryPool {
 public:
  static const size_t page_size;

  static HostMemoryPool &get_instance();

  void *allocate(std::size_t size,
                 std::size_t alignment,
                 bool exclusive = false);
  void release(std::size_t size, void *ptr);
  void reset();
  HostMemoryPool();
  ~HostMemoryPool();

 protected:
  void *allocate_raw_memory(std::size_t size);
  void deallocate_raw_memory(void *ptr);

  // All the raw memory allocated from OS/Driver
  // We need to keep track of them to guarantee that they are freed
  std::map<void *, std::size_t> raw_memory_chunks_;

  std::unique_ptr<UnifiedAllocator> allocator_;
  std::mutex mut_allocation_;

  friend class UnifiedAllocator;
};

}  // namespace gstaichi::lang
