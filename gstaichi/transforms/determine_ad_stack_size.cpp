#include "gstaichi/ir/analysis.h"
#include "gstaichi/ir/control_flow_graph.h"
#include "gstaichi/ir/ir.h"
#include "gstaichi/ir/statements.h"
#include "gstaichi/ir/transforms.h"

#include <queue>
#include <unordered_map>

namespace gstaichi::lang {

namespace irpass {

bool determine_ad_stack_size(IRNode *root, const CompileConfig &config) {
  if (irpass::analysis::gather_statements(root, [&](Stmt *s) {
        if (auto ad_stack = s->cast<AdStackAllocaStmt>()) {
          return ad_stack->max_size == 0;  // adaptive
        }
        return false;
      }).empty()) {
    return false;  // no AD-stacks with adaptive size
  }
  auto cfg = analysis::build_cfg(root);
  cfg->simplify_graph();
  cfg->determine_ad_stack_size(config.default_ad_stack_size);
  return true;
}

}  // namespace irpass

}  // namespace gstaichi::lang
