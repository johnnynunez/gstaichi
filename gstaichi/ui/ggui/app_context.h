#pragma once
#include "gstaichi/ui/common/app_config.h"
#include <memory>
#include "gstaichi/rhi/vulkan/vulkan_device_creator.h"
#include "gstaichi/rhi/vulkan/vulkan_loader.h"
#include "gstaichi/rhi/vulkan/vulkan_device.h"
#ifdef TI_WITH_METAL
#include "gstaichi/rhi/metal/metal_device.h"
#endif
#include "gstaichi/ui/ggui/swap_chain.h"
#ifdef ANDROID
#include <android/native_window.h>
#endif

namespace gstaichi::lang {
class Program;
}  // namespace gstaichi::lang

namespace gstaichi::ui {

#ifdef ANDROID
using GsTaichiWindow = ANativeWindow;
#else
using GsTaichiWindow = GLFWwindow;
#endif

namespace vulkan {

class TI_DLL_EXPORT AppContext {
 public:
  void init_with_vulkan(lang::Program *prog,
                        GsTaichiWindow *window,
                        const AppConfig &config);
  void init_with_metal(lang::Program *prog,
                       GsTaichiWindow *window,
                       const AppConfig &config);
  ~AppContext();

  GsTaichiWindow *gstaichi_window() const;
  lang::Program *prog() const;

  gstaichi::lang::GraphicsDevice &device();
  const gstaichi::lang::GraphicsDevice &device() const;
  bool requires_export_sharing() const;

  AppConfig config;

  struct RasterPipelineConfig {
    std::string frag_path;
    std::string vert_path;
    gstaichi::lang::TopologyType prim_topology{
        gstaichi::lang::TopologyType::Triangles};
    bool depth{false};
    gstaichi::lang::PolygonMode polygon_mode{gstaichi::lang::PolygonMode::Fill};
    bool blend{true};
    bool vbo_instanced{false};
  };

  // Get a raster pipeline with the given fragment shader and vertex shader &
  // options.
  // - This function will cache the pipeline for future use.
  // - This function will use the default GGUI vertex input format
  gstaichi::lang::Pipeline *get_raster_pipeline(
      const RasterPipelineConfig &config);

  // Get a raster pipeline with the given fragment shader and vertex shader &
  // options.
  // - This function will cache the pipeline for future use
  // - This function will use the provided vertex input format
  gstaichi::lang::Pipeline *get_customized_raster_pipeline(
      const RasterPipelineConfig &config,
      const std::vector<gstaichi::lang::VertexInputBinding> &vertex_inputs,
      const std::vector<gstaichi::lang::VertexInputAttribute> &vertex_attribs);

  // Get a compute pipeline with the given compute shader
  // - This function will cache the pipeline for future use
  gstaichi::lang::Pipeline *get_compute_pipeline(const std::string &shader_path);

  VkSurfaceKHR get_native_surface() const {
    return native_surface_;
  }

 private:
  std::unique_ptr<gstaichi::lang::vulkan::VulkanDeviceCreator>
      embedded_vulkan_device_{nullptr};

  VkSurfaceKHR native_surface_{VK_NULL_HANDLE};

  std::unordered_map<std::string, gstaichi::lang::UPipeline> pipelines_;

  // not owned
  gstaichi::lang::GraphicsDevice *graphics_device_{nullptr};

  GsTaichiWindow *gstaichi_window_{nullptr};

  lang::Program *prog_{nullptr};
};

}  // namespace vulkan

}  // namespace gstaichi::ui
