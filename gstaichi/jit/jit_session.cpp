#include "gstaichi/jit/jit_session.h"

#ifdef TI_WITH_LLVM
#include "llvm/IR/DataLayout.h"
#endif

namespace gstaichi::lang {

class ProgramImpl;

#ifdef TI_WITH_LLVM
std::unique_ptr<JITSession> create_llvm_jit_session_cpu(
    GsTaichiLLVMContext *tlctx,
    const CompileConfig &config,
    Arch arch);

std::unique_ptr<JITSession> create_llvm_jit_session_cuda(
    GsTaichiLLVMContext *tlctx,
    const CompileConfig &config,
    Arch arch,
    ProgramImpl *program_impl);

std::unique_ptr<JITSession> create_llvm_jit_session_amdgpu(
    GsTaichiLLVMContext *tlctx,
    const CompileConfig &config,
    Arch arch);
#endif

JITSession::JITSession(GsTaichiLLVMContext *tlctx, const CompileConfig &config)
    : tlctx_(tlctx), config_(config) {
}

std::unique_ptr<JITSession> JITSession::create(GsTaichiLLVMContext *tlctx,
                                               const CompileConfig &config,
                                               Arch arch,
                                               ProgramImpl *program_impl) {
#ifdef TI_WITH_LLVM
  if (arch_is_cpu(arch)) {
    return create_llvm_jit_session_cpu(tlctx, config, arch);
  } else if (arch == Arch::cuda) {
#if defined(TI_WITH_CUDA)
    return create_llvm_jit_session_cuda(tlctx, config, arch, program_impl);
#else
    TI_NOT_IMPLEMENTED
#endif
  } else if (arch == Arch::amdgpu) {
#ifdef TI_WITH_AMDGPU
    return create_llvm_jit_session_amdgpu(tlctx, config, arch);
#else
    TI_NOT_IMPLEMENTED
#endif
  }
#else
  TI_ERROR("Llvm disabled");
#endif
  return nullptr;
}

}  // namespace gstaichi::lang
