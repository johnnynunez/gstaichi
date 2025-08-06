#include "gstaichi/ir/ir.h"
#include "gstaichi/ir/analysis.h"
#include "gstaichi/ir/visitors.h"

namespace gstaichi::lang {

class FieldsRegisteredChecker : public BasicStmtVisitor {
 public:
  using BasicStmtVisitor::visit;

  FieldsRegisteredChecker() {
    allow_undefined_visitor = true;
    invoke_default_visitor = true;
  }

  void preprocess_container_stmt(Stmt *stmt) override {
    TI_ASSERT(stmt->fields_registered);
  }

  void visit(Stmt *stmt) override {
    TI_ASSERT(stmt->fields_registered);
  }

  static void run(IRNode *root) {
    FieldsRegisteredChecker checker;
    root->accept(&checker);
  }
};

namespace irpass::analysis {
void check_fields_registered(IRNode *root) {
  return FieldsRegisteredChecker::run(root);
}
}  // namespace irpass::analysis

}  // namespace gstaichi::lang
