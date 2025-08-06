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

namespace gstaichi::ui {

namespace vulkan {

class Circles final : public Renderable {
 public:
  Circles(AppContext *app_context, VertexAttributes vbo_attrs);
  void update_data(const CirclesInfo &info);

  void record_this_frame_commands(lang::CommandList *command_list) override;

 private:
  struct UniformBufferObject {
    alignas(16) glm::vec3 color;
    int use_per_vertex_color;
    int use_per_vertex_radius;
    float radius;
    float window_width;
    float window_height;
  };
};

}  // namespace vulkan

}  // namespace gstaichi::ui
