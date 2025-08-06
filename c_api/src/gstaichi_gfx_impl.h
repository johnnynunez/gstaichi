#pragma once

#include "gstaichi_core_impl.h"
#include "gstaichi/runtime/gfx/runtime.h"
#include "gstaichi/common/virtual_dir.h"

class GfxRuntime;

class GfxRuntime : public Runtime {
 public:
  GfxRuntime(gstaichi::Arch arch);
  virtual gstaichi::lang::gfx::GfxRuntime &get_gfx_runtime() = 0;

  virtual Error create_aot_module(const gstaichi::io::VirtualDir *dir,
                                  TiAotModule &out) override final;
  virtual void buffer_copy(const gstaichi::lang::DevicePtr &dst,
                           const gstaichi::lang::DevicePtr &src,
                           size_t size) override final;
  virtual void copy_image(
      const gstaichi::lang::DeviceAllocation &dst,
      const gstaichi::lang::DeviceAllocation &src,
      const gstaichi::lang::ImageCopyParams &params) override final;
  virtual void track_image(const gstaichi::lang::DeviceAllocation &image,
                           gstaichi::lang::ImageLayout layout) override final;
  virtual void untrack_image(
      const gstaichi::lang::DeviceAllocation &image) override final;
  virtual void transition_image(
      const gstaichi::lang::DeviceAllocation &image,
      gstaichi::lang::ImageLayout layout) override final;
  virtual void flush() override final;
  virtual void wait() override final;
};
