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

class Triangles final : public Renderable {
 public:
  Triangles(AppContext *app_context, VertexAttributes vbo_attrs);

  void update_data(const TrianglesInfo &info);

 private:
  struct UniformBufferObject {
    alignas(16) glm::vec3 color;
    int use_per_vertex_color;
  };
};

}  // namespace vulkan

}  // namespace gstaichi::ui
