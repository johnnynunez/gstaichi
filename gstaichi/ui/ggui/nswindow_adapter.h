#pragma once

#include "gstaichi/rhi/common/window_system.h"
#include "gstaichi/rhi/metal/metal_device.h"

namespace gstaichi::ui {

namespace vulkan {

using namespace gstaichi::lang;
using namespace gstaichi::lang::metal;

struct NSWindowAdapter {
  void set_content_view(GLFWwindow *glfw_window, metal::MetalSurface *mtl_surf);
};

}  // namespace vulkan

}  // namespace gstaichi::ui
