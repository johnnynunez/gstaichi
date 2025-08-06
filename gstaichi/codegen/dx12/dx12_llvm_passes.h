
#pragma once

#include <string>
#include <vector>

namespace llvm {
class Function;
class Module;
class Type;
class GlobalVariable;
}  // namespace llvm

namespace gstaichi::lang {
struct CompileConfig;

namespace directx12 {

void mark_function_as_cs_entry(llvm::Function *);
bool is_cs_entry(llvm::Function *);
void set_num_threads(llvm::Function *, unsigned x, unsigned y, unsigned z);
llvm::GlobalVariable *createGlobalVariableForResource(llvm::Module &M,
                                                      const char *Name,
                                                      llvm::Type *Ty);

std::vector<uint8_t> global_optimize_module(llvm::Module *module,
                                            const CompileConfig &config);

extern const char *NumWorkGroupsCBName;

}  // namespace directx12
}  // namespace gstaichi::lang

namespace llvm {
class ModulePass;
class PassRegistry;
class Function;

/// Initializer for DXIL-prepare
void initializeGsTaichiRuntimeContextLowerPass(PassRegistry &);

/// Pass to convert modules into DXIL-compatable modules
ModulePass *createGsTaichiRuntimeContextLowerPass();

/// Initializer for gstaichi intrinsic lower.
void initializeGsTaichiIntrinsicLowerPass(PassRegistry &);

/// Pass to lower gstaichi intrinsic into DXIL intrinsic.
ModulePass *createGsTaichiIntrinsicLowerPass(
    const gstaichi::lang::CompileConfig *config);

}  // namespace llvm
