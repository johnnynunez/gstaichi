#pragma once
#ifdef TI_WITH_VULKAN

#include "gstaichi_core_impl.h"
#include "gstaichi_gfx_impl.h"
#include "gstaichi/rhi/vulkan/vulkan_loader.h"
#include "gstaichi/rhi/vulkan/vulkan_device.h"
#include "gstaichi/rhi/vulkan/vulkan_device_creator.h"

class VulkanRuntime;
class VulkanRuntimeImported;
class VulkanRuntimeOwned;
class VulkanContext;

class VulkanRuntime : public GfxRuntime {
 public:
  VulkanRuntime();

  gstaichi::lang::vulkan::VulkanDevice &get_vk();
  virtual TiImage allocate_image(
      const gstaichi::lang::ImageParams &params) override final;
  virtual void free_image(TiImage image) override final;
};
class VulkanRuntimeImported : public VulkanRuntime {
  // A dirty workaround to ensure the device is fully initialized before
  // construction of `gfx_runtime_`.
  struct Workaround {
    gstaichi::lang::vulkan::VulkanDevice vk_device;
    Workaround(uint32_t api_version,
               const gstaichi::lang::vulkan::VulkanDevice::Params &params);
  } inner_;
  gstaichi::lang::gfx::GfxRuntime gfx_runtime_;

 public:
  VulkanRuntimeImported(
      uint32_t api_version,
      const gstaichi::lang::vulkan::VulkanDevice::Params &params);

  virtual gstaichi::lang::Device &get() override final;
  virtual gstaichi::lang::gfx::GfxRuntime &get_gfx_runtime() override final;
};
class VulkanRuntimeOwned : public VulkanRuntime {
  gstaichi::lang::vulkan::VulkanDeviceCreator vk_device_creator_;
  gstaichi::lang::gfx::GfxRuntime gfx_runtime_;

 public:
  VulkanRuntimeOwned();
  VulkanRuntimeOwned(
      const gstaichi::lang::vulkan::VulkanDeviceCreator::Params &params);

  virtual gstaichi::lang::Device &get() override final;
  virtual gstaichi::lang::gfx::GfxRuntime &get_gfx_runtime() override final;
};

gstaichi::lang::vulkan::VulkanDeviceCreator::Params
make_vulkan_runtime_creator_params();

#endif  // TI_WITH_VULKAN
