#pragma once

#ifdef TI_WITH_DX11

#include "gstaichi/runtime/gfx/runtime.h"
#include "gstaichi/runtime/gfx/snode_tree_manager.h"
#include "gstaichi/runtime/program_impls/gfx/gfx_program.h"

namespace gstaichi::lang {

class Dx11ProgramImpl : public GfxProgramImpl {
 public:
  Dx11ProgramImpl(CompileConfig &config);

  void materialize_runtime(KernelProfilerBase *profiler,
                           uint64 **result_buffer_ptr) override;
};

}  // namespace gstaichi::lang

#endif
