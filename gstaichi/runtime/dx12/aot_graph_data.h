#pragma once
#include "gstaichi/aot/graph_data.h"

namespace gstaichi {
namespace lang {
namespace directx12 {
class KernelImpl : public aot::Kernel {
 public:
  explicit KernelImpl() {
  }

  void launch(LaunchContextBuilder &ctx) override {
  }
};
}  // namespace directx12
}  // namespace lang
}  // namespace gstaichi
