#pragma once

#include <iostream>
#include <fstream>
#include <stdexcept>
#include <algorithm>
#include <chrono>
#include <vector>
#include <cstring>
#include <cstdlib>
#include <cstdint>
#include <array>
#include <optional>
#include <set>
#include "gstaichi/ui/utils/utils.h"
#include "gstaichi/ui/ggui/vertex.h"

#include "gstaichi/ui/ggui/app_context.h"
#include "gstaichi/ui/ggui/swap_chain.h"
#include "gstaichi/ui/ggui/renderable.h"
#include "gstaichi/program/field_info.h"
#include "gstaichi/ui/common/canvas_base.h"
#include "gstaichi/rhi/device.h"

namespace gstaichi::ui {

namespace vulkan {

class SetImage final : public Renderable {
 public:
  struct UniformBufferObject {
    glm::vec2 lower_bound;
    glm::vec2 upper_bound;
    // in non_packed_mode,
    // the actual image is only a corner of the whole image
    float x_factor{1.0};
    float y_factor{1.0};
    int transpose{0};
  };

  SetImage(AppContext *app_context, VertexAttributes vbo_attrs);

  void record_this_frame_commands(
      gstaichi::lang::CommandList *command_list) final;

  void update_data(const SetImageInfo &info);

  void update_data(gstaichi::lang::Texture *tex);

 private:
  int width_{0};
  int height_{0};

  gstaichi::lang::DeviceImageUnique texture_{nullptr};

  gstaichi::lang::BufferFormat format_;

 private:
  void resize_texture(int width, int height, gstaichi::lang::BufferFormat format);

  void update_ubo(float x_factor, float y_factor, bool transpose);
};

}  // namespace vulkan

}  // namespace gstaichi::ui
