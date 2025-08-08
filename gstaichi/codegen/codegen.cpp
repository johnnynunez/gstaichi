// Driver class for kernel codegen

#include "codegen.h"

#if defined(TI_WITH_LLVM)
#include "gstaichi/codegen/cpu/codegen_cpu.h"
#include "gstaichi/runtime/program_impls/llvm/llvm_program.h"
#endif
#if defined(TI_WITH_CUDA)
#include "gstaichi/codegen/cuda/codegen_cuda.h"
#endif
#if defined(TI_WITH_AMDGPU)
#include "gstaichi/codegen/amdgpu/codegen_amdgpu.h"
#endif
#include "gstaichi/system/timer.h"
#include "gstaichi/ir/analysis.h"
#include "gstaichi/ir/transforms.h"
#include "gstaichi/analysis/offline_cache_util.h"

namespace gstaichi::lang {

KernelCodeGen::KernelCodeGen(const CompileConfig &compile_config,
                             const Kernel *kernel,
                             IRNode *ir,
                             GsTaichiLLVMContext &tlctx)
    : prog(kernel->program),
      kernel(kernel),
      ir(ir),
      compile_config_(compile_config),
      tlctx_(tlctx) {
}

std::unique_ptr<KernelCodeGen> KernelCodeGen::create(
    const CompileConfig &compile_config,
    const Kernel *kernel,
    IRNode *ir,
    GsTaichiLLVMContext &tlctx) {
#ifdef TI_WITH_LLVM
  const auto arch = compile_config.arch;
  if (arch_is_cpu(arch)) {
    return std::make_unique<KernelCodeGenCPU>(compile_config, kernel, ir,
                                              tlctx);
  } else if (arch == Arch::cuda) {
#if defined(TI_WITH_CUDA)
    return std::make_unique<KernelCodeGenCUDA>(compile_config, kernel, ir,
                                               tlctx);
#else
    TI_NOT_IMPLEMENTED
#endif
  } else if (arch == Arch::amdgpu) {
#if defined(TI_WITH_AMDGPU)
    return std::make_unique<KernelCodeGenAMDGPU>(compile_config, kernel, ir,
                                                 tlctx);
#else
    TI_NOT_IMPLEMENTED
#endif
  } else {
    TI_NOT_IMPLEMENTED
  }
#else
  TI_ERROR("Llvm disabled");
#endif
}
#ifdef TI_WITH_LLVM

LLVMCompiledKernel KernelCodeGen::compile_kernel_to_module() {
  auto block = dynamic_cast<Block *>(ir);
  auto &worker = get_llvm_program(kernel->program)->compilation_workers;
  TI_ASSERT(block);

  auto &offloads = block->statements;
  std::vector<std::unique_ptr<LLVMCompiledTask>> data(offloads.size());
  for (int i = 0; i < offloads.size(); i++) {
    auto compile_func = [&, i] {
      tlctx_.fetch_this_thread_struct_module();
      auto offload = irpass::analysis::clone(offloads[i].get());
      irpass::re_id(offload.get());

      Block blk;
      blk.insert(std::move(offload));
      auto new_data = this->compile_task(i, compile_config_, nullptr, &blk);
      data[i] = std::make_unique<LLVMCompiledTask>(std::move(new_data));
    };
    worker.enqueue(compile_func);
  }
  worker.flush();

  auto llvm_compiled_kernel = tlctx_.link_compiled_tasks(std::move(data));
  optimize_module(llvm_compiled_kernel.module.get());
  return llvm_compiled_kernel;
}

#endif
}  // namespace gstaichi::lang
