#pragma once
#ifdef TI_WITH_METAL
#include "gstaichi_core_impl.h"
#include "gstaichi_gfx_impl.h"
#include "gstaichi/rhi/metal/metal_device.h"

namespace capi {

class MetalRuntime;

class MetalRuntime : public GfxRuntime {
 private:
  std::unique_ptr<gstaichi::lang::metal::MetalDevice> mtl_device_;
  gstaichi::lang::gfx::GfxRuntime gfx_runtime_;

 public:
  explicit MetalRuntime();
  explicit MetalRuntime(
      std::unique_ptr<gstaichi::lang::metal::MetalDevice> &&mtl_device);

  gstaichi::lang::Device &get() override;
  gstaichi::lang::gfx::GfxRuntime &get_gfx_runtime() override;

  gstaichi::lang::metal::MetalDevice &get_mtl();
  virtual TiImage allocate_image(
      const gstaichi::lang::ImageParams &params) override final;
  virtual void free_image(TiImage image) override final;
};

}  // namespace capi

#endif  // TI_WITH_METAL
