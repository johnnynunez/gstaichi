#include "gtest/gtest.h"
#include "gstaichi/rhi/opengl/opengl_api.h"
#include "tests/cpp/aot/gfx_utils.h"

using namespace gstaichi;
using namespace lang;

TEST(GfxAotTest, OpenglDenseField) {
  if (!opengl::is_opengl_api_available()) {
    return;
  }

  auto device = gstaichi::lang::opengl::make_opengl_device();

  aot_test_utils::run_dense_field_kernel(Arch::opengl, device.get());
}

TEST(GfxAotTest, OpenglKernelTest1) {
  if (!opengl::is_opengl_api_available()) {
    return;
  }

  auto device = gstaichi::lang::opengl::make_opengl_device();

  aot_test_utils::run_kernel_test1(Arch::opengl, device.get());
}

TEST(GfxAotTest, OpenglKernelTest2) {
  if (!opengl::is_opengl_api_available()) {
    return;
  }

  auto device = gstaichi::lang::opengl::make_opengl_device();

  aot_test_utils::run_kernel_test2(Arch::opengl, device.get());
}
