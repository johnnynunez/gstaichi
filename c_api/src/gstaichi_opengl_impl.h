#pragma once
#ifdef TI_WITH_OPENGL

#include "gstaichi_gfx_impl.h"
#include "gstaichi/rhi/opengl/opengl_api.h"
#include "gstaichi/rhi/opengl/opengl_device.h"

class OpenglRuntime : public GfxRuntime {
 private:
  gstaichi::lang::opengl::GLDevice device_;
  gstaichi::lang::gfx::GfxRuntime gfx_runtime_;

 public:
  OpenglRuntime();
  virtual gstaichi::lang::Device &get() override final;
  virtual gstaichi::lang::gfx::GfxRuntime &get_gfx_runtime() override final;
  gstaichi::lang::opengl::GLDevice &get_gl() {
    return device_;
  }
};

#endif  // TI_WITH_OPENGL
