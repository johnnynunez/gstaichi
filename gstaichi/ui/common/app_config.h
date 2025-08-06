#pragma once

#include <string>
#include "gstaichi/ui/utils/utils.h"
#include "gstaichi/rhi/arch.h"

namespace gstaichi {
namespace ui {

struct AppConfig {
  std::string name;
  int width{0};
  int height{0};
  int window_pos_x{0};
  int window_pos_y{0};
  bool vsync{false};
  bool show_window{true};
  double fps_limit{1000.0};
  std::string package_path;
  Arch ti_arch;
  Arch ggui_arch{Arch::vulkan};
};

}  // namespace ui
}  // namespace gstaichi
