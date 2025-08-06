#pragma once

#include "gstaichi/runtime/gfx/runtime.h"
#include "gstaichi/runtime/gfx/snode_tree_manager.h"
#include "gstaichi/program/program_impl.h"
#include "gstaichi/runtime/program_impls/gfx/gfx_program.h"

namespace gstaichi::lang {

class OpenglProgramImpl : public GfxProgramImpl {
 public:
  explicit OpenglProgramImpl(CompileConfig &config);

  void finalize() override;

  void materialize_runtime(KernelProfilerBase *profiler,
                           uint64 **result_buffer_ptr) override;
};

}  // namespace gstaichi::lang
