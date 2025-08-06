

#include "dx12_llvm_passes.h"

#include "llvm/Pass.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/ADT/SmallVector.h"
#include "llvm/IR/Instructions.h"
#include "llvm/ADT/STLExtras.h"
#include "llvm/Transforms/Utils/ModuleUtils.h"

#include "gstaichi/program/compile_config.h"
#include "gstaichi/runtime/llvm/llvm_context.h"

using namespace llvm;
using namespace gstaichi::lang::directx12;

#define DEBUG_TYPE "dxil-gstaichi-runtime-context-lower"

namespace {

class GsTaichiRuntimeContextLower : public ModulePass {
 public:
  bool runOnModule(Module &M) override {
    // TODO: lower gstaichi RuntimeContext into DXIL resources.
    return true;
  }

  GsTaichiRuntimeContextLower() : ModulePass(ID) {
    initializeGsTaichiRuntimeContextLowerPass(*PassRegistry::getPassRegistry());
  }

  static char ID;  // Pass identification.
 private:
};
char GsTaichiRuntimeContextLower::ID = 0;

}  // end anonymous namespace

INITIALIZE_PASS(GsTaichiRuntimeContextLower,
                DEBUG_TYPE,
                "Lower gstaichi RuntimeContext",
                false,
                false)

llvm::ModulePass *llvm::createGsTaichiRuntimeContextLowerPass() {
  return new GsTaichiRuntimeContextLower();
}
