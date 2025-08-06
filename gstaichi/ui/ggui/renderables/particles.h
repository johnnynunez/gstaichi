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
#include "gstaichi/ui/ggui/scene.h"

namespace gstaichi::ui {

namespace vulkan {

class Particles final : public Renderable {
 public:
  Particles(AppContext *app_context, VertexAttributes vbo_attrs);

  void update_data(const ParticlesInfo &info);

  void update_scene_data(DevicePtr ssbo_ptr, DevicePtr ubo_ptr) override;

  void record_this_frame_commands(lang::CommandList *command_list) override;

 private:
  DevicePtr lights_ssbo_ptr;
  DevicePtr scene_ubo_ptr;

  struct UBORenderable {
    alignas(16) glm::vec3 color;
    int use_per_vertex_color;
    int use_per_vertex_radius;
    float radius;
  };
};

}  // namespace vulkan

}  // namespace gstaichi::ui
