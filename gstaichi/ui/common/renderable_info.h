#pragma once

#include "gstaichi/ui/ggui/vertex.h"
#include "gstaichi/program/field_info.h"
#include "gstaichi/ui/utils/utils.h"

namespace gstaichi::ui {

struct RenderableInfo {
  FieldInfo vbo;
  FieldInfo indices;
  bool has_per_vertex_color{false};
  bool has_per_vertex_radius{false};
  VertexAttributes vbo_attrs{VboHelpers::all()};
  bool has_user_customized_draw{false};
  int draw_vertex_count{0};
  int draw_first_vertex{0};
  int draw_index_count{0};
  int draw_first_index{0};
  gstaichi::lang::PolygonMode display_mode{gstaichi::lang::PolygonMode::Fill};
};

}  // namespace gstaichi::ui
