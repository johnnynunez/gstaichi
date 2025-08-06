#pragma once
#include "gstaichi/ui/common/scene_base.h"

namespace gstaichi::ui {

namespace vulkan {

class Scene final : public SceneBase {
 public:
  void set_camera(const Camera &camera) override;
  void lines(const SceneLinesInfo &info) override;
  void mesh(const MeshInfo &info) override;
  void particles(const ParticlesInfo &info) override;
  void point_light(glm::vec3 pos, glm::vec3 color) override;
  void ambient_light(glm::vec3 color) override;
};

}  // namespace vulkan

}  // namespace gstaichi::ui
