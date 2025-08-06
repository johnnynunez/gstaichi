#include "gtest/gtest.h"
#include "gstaichi/rhi/vulkan/vulkan_device.h"
#include "gstaichi/rhi/vulkan/vulkan_device_creator.h"
#include "gstaichi/rhi/vulkan/vulkan_loader.h"
#include "tests/cpp/aot/gfx_utils.h"

using namespace gstaichi;
using namespace lang;

TEST(DeviceTest, ViewDevAllocAsNdarray) {
  // Otherwise will segfault on macOS VM,
  // where Vulkan is installed but no devices are present
  if (!vulkan::is_vulkan_api_available()) {
    return;
  }

  // Create GsTaichi Device for computation
  lang::vulkan::VulkanDeviceCreator::Params evd_params;
  evd_params.api_version = std::nullopt;
  auto embedded_device =
      std::make_unique<gstaichi::lang::vulkan::VulkanDeviceCreator>(evd_params);
  gstaichi::lang::vulkan::VulkanDevice *device_ =
      static_cast<gstaichi::lang::vulkan::VulkanDevice *>(
          embedded_device->device());

  aot_test_utils::view_devalloc_as_ndarray(device_);
}
