#ifdef TI_WITH_METAL
#include "gstaichi_metal_impl.h"
#include "gstaichi/rhi/metal/metal_device.h"
#include "gstaichi/runtime/gfx/runtime.h"

namespace capi {

MetalRuntime::MetalRuntime()
    : MetalRuntime(std::unique_ptr<gstaichi::lang::metal::MetalDevice>(
          gstaichi::lang::metal::MetalDevice::create())) {}

MetalRuntime::MetalRuntime(
    std::unique_ptr<gstaichi::lang::metal::MetalDevice> &&mtl_device)
    : GfxRuntime(gstaichi::Arch::metal), mtl_device_(std::move(mtl_device)),
      gfx_runtime_(gstaichi::lang::gfx::GfxRuntime::Params{mtl_device_.get()}) {}

gstaichi::lang::Device &MetalRuntime::get() {
  return static_cast<gstaichi::lang::Device &>(*mtl_device_);
}
gstaichi::lang::gfx::GfxRuntime &MetalRuntime::get_gfx_runtime() {
  return gfx_runtime_;
}

gstaichi::lang::metal::MetalDevice &MetalRuntime::get_mtl() {
  return *mtl_device_;
}

TiImage MetalRuntime::allocate_image(const gstaichi::lang::ImageParams &params) {
  gstaichi::lang::DeviceAllocation devalloc =
      get_gfx_runtime().create_image(params);
  return devalloc2devimg(*this, devalloc);
}
void MetalRuntime::free_image(TiImage image) {
  gstaichi::lang::DeviceAllocation devimg = devimg2devalloc(*this, image);
  get_mtl().destroy_image(devimg);
  get_gfx_runtime().untrack_image(devimg);
}

} // namespace capi

// -----------------------------------------------------------------------------

inline capi::MetalRuntime &ti_runtime2mtl_runtime(TiRuntime runtime) {
  Runtime *runtime2 = (Runtime *)runtime;
  return *runtime2->as_mtl();
}

TiRuntime
ti_import_metal_runtime(const TiMetalRuntimeInteropInfo *interop_info) {
  TiRuntime out = TI_NULL_HANDLE;
  TI_CAPI_TRY_CATCH_BEGIN();
  TI_CAPI_ARGUMENT_NULL_RV(interop_info);
  auto mtl_device = std::make_unique<gstaichi::lang::metal::MetalDevice>(
      (MTLDevice_id)interop_info->device);
  out = (TiRuntime) new capi::MetalRuntime(std::move(mtl_device));
  TI_CAPI_TRY_CATCH_END();
  return out;
}

void ti_export_metal_runtime(TiRuntime runtime,
                             TiMetalRuntimeInteropInfo *interop_info) {
  TI_CAPI_TRY_CATCH_BEGIN()
  TI_CAPI_ARGUMENT_NULL(runtime);
  TI_CAPI_ARGUMENT_NULL(interop_info);
  capi::MetalRuntime &runtime2 = ti_runtime2mtl_runtime(runtime);
  interop_info->bundle = TI_NULL_HANDLE;
  interop_info->device = (TiMtlDevice)runtime2.get_mtl().mtl_device();
  TI_CAPI_TRY_CATCH_END()
}

TiMemory ti_import_metal_memory(TiRuntime runtime,
                                const TiMetalMemoryInteropInfo *interop_info) {
  TiMemory out = TI_NULL_HANDLE;
  TI_CAPI_TRY_CATCH_BEGIN();
  TI_CAPI_ARGUMENT_NULL_RV(runtime);
  TI_CAPI_ARGUMENT_NULL_RV(interop_info);
  capi::MetalRuntime &runtime2 = ti_runtime2mtl_runtime(runtime);
  gstaichi::lang::DeviceAllocation devalloc =
      runtime2.get_mtl().import_mtl_buffer((MTLBuffer_id)interop_info->buffer);
  out = devalloc2devmem(runtime2, devalloc);
  TI_CAPI_TRY_CATCH_END();
  return out;
}

void ti_export_metal_memory(TiRuntime runtime, TiMemory memory,
                            TiMetalMemoryInteropInfo *interop_info) {
  TI_CAPI_TRY_CATCH_BEGIN();
  TI_CAPI_ARGUMENT_NULL(runtime);
  TI_CAPI_ARGUMENT_NULL(memory);
  TI_CAPI_ARGUMENT_NULL(interop_info);
  capi::MetalRuntime &runtime2 = ti_runtime2mtl_runtime(runtime);
  gstaichi::lang::DeviceAllocation devalloc = devmem2devalloc(runtime2, memory);
  gstaichi::lang::metal::MetalMemory &memory =
      runtime2.get_mtl().get_memory(devalloc.alloc_id);
  interop_info->buffer = (TiMtlBuffer)memory.mtl_buffer();
  TI_CAPI_TRY_CATCH_END();
}

TiImage ti_import_metal_image(TiRuntime runtime,
                              const TiMetalImageInteropInfo *interop_info) {
  TiImage out = TI_NULL_HANDLE;
  TI_CAPI_TRY_CATCH_BEGIN();
  TI_CAPI_ARGUMENT_NULL_RV(runtime);
  TI_CAPI_ARGUMENT_NULL_RV(interop_info);
  capi::MetalRuntime &runtime2 = ti_runtime2mtl_runtime(runtime);
  gstaichi::lang::DeviceAllocation devalloc =
      runtime2.get_mtl().import_mtl_texture(
          (MTLTexture_id)interop_info->texture);
  out = devalloc2devimg(runtime2, devalloc);
  TI_CAPI_TRY_CATCH_END();
  return out;
}

TI_DLL_EXPORT void TI_API_CALL ti_export_metal_image(
    TiRuntime runtime, TiImage image, TiMetalImageInteropInfo *interop_info) {
  TI_CAPI_TRY_CATCH_BEGIN();
  TI_CAPI_ARGUMENT_NULL(runtime);
  TI_CAPI_ARGUMENT_NULL(image);
  TI_CAPI_ARGUMENT_NULL(interop_info);
  capi::MetalRuntime &runtime2 = ti_runtime2mtl_runtime(runtime);
  gstaichi::lang::DeviceAllocation devalloc = devimg2devalloc(runtime2, image);
  gstaichi::lang::metal::MetalImage &image =
      runtime2.get_mtl().get_image(devalloc.alloc_id);
  interop_info->texture = (TiMtlTexture)image.mtl_texture();
  TI_CAPI_TRY_CATCH_END();
}

#endif // TI_WITH_METAL
