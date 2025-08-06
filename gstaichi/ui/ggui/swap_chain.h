#pragma once

#include <gstaichi/rhi/device.h>

namespace gstaichi::ui {
namespace vulkan {

class TI_DLL_EXPORT SwapChain {
 public:
  void init(class AppContext *app_context);
  ~SwapChain();

  uint32_t width();
  uint32_t height();

  gstaichi::lang::Surface &surface();
  gstaichi::lang::DeviceAllocation depth_allocation();

  void resize(uint32_t width, uint32_t height);

  bool copy_depth_buffer_to_ndarray(gstaichi::lang::DevicePtr &arr_dev_ptr);

  std::vector<uint32_t> &dump_image_buffer();

  void write_image(const std::string &filename);

 private:
  void create_depth_resources();
  void create_image_resources();

  std::unique_ptr<gstaichi::lang::Surface> surface_{nullptr};
  gstaichi::lang::DeviceImageUnique depth_allocation_{nullptr};

  std::vector<uint32_t> image_buffer_data_;

  gstaichi::lang::DeviceAllocationUnique depth_buffer_{nullptr};
  gstaichi::lang::DeviceAllocationUnique screenshot_buffer_{nullptr};

  class AppContext *app_context_;

  uint32_t curr_width_;
  uint32_t curr_height_;
};

}  // namespace vulkan

}  // namespace gstaichi::ui
