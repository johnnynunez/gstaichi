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
#include <memory>

#include "gstaichi/ui/utils/utils.h"
#include "gstaichi/ui/ggui/vertex.h"
#include "gstaichi/ui/ggui/app_context.h"
#include "gstaichi/ui/ggui/swap_chain.h"
#include "gstaichi/ui/ggui/renderable.h"
#include "gstaichi/ui/common/canvas_base.h"

#include "gstaichi/ui/ggui/gui.h"
#include "gstaichi/ui/ggui/gui_metal.h"
#include "gstaichi/ui/ggui/renderer.h"

#include "gstaichi/ui/ggui/renderables/set_image.h"
#include "gstaichi/ui/ggui/renderables/triangles.h"
#include "gstaichi/ui/ggui/renderables/mesh.h"
#include "gstaichi/ui/ggui/renderables/particles.h"
#include "gstaichi/ui/ggui/renderables/circles.h"
#include "gstaichi/ui/ggui/renderables/lines.h"

namespace gstaichi::ui {

namespace vulkan {

class TI_DLL_EXPORT Canvas final : public CanvasBase {
 public:
  explicit Canvas(Renderer *renderer);

  void set_background_color(const glm::vec3 &color) override;

  void set_image(const SetImageInfo &info) override;

  void set_image(gstaichi::lang::Texture *tex) override;

  void triangles(const TrianglesInfo &info) override;

  void circles(const CirclesInfo &info) override;

  void lines(const LinesInfo &info) override;

  void scene(SceneBase *scene_base) override;

 private:
  Renderer *renderer_;
};

}  // namespace vulkan

}  // namespace gstaichi::ui
