#include "gtest/gtest.h"
#include "gstaichi/rhi/opengl/opengl_api.h"
#include "tests/cpp/aot/gfx_utils.h"

using namespace gstaichi;
using namespace lang;

TEST(DeviceTest, GLDevice) {
  if (!opengl::is_opengl_api_available()) {
    return;
  }

  auto device_ = gstaichi::lang::opengl::make_opengl_device();

  aot_test_utils::view_devalloc_as_ndarray(device_.get());
}
