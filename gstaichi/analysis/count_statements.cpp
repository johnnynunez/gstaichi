#include "gstaichi/ir/ir.h"
#include "gstaichi/ir/analysis.h"
#include "gstaichi/ir/visitors.h"

namespace gstaichi::lang {

// Count all statements (including containers)
class StmtCounter : public BasicStmtVisitor {
 private:
  StmtCounter() {
    counter_ = 0;
    allow_undefined_visitor = true;
    invoke_default_visitor = true;
  }

  using BasicStmtVisitor::visit;

 public:
  void preprocess_container_stmt(Stmt *stmt) override {
    counter_++;
  }

  void visit(Stmt *stmt) override {
    counter_++;
  }

  static int run(IRNode *root) {
    StmtCounter stmt_counter;
    root->accept(&stmt_counter);
    return stmt_counter.counter_;
  }

 private:
  int counter_;
};

namespace irpass::analysis {
int count_statements(IRNode *root) {
  TI_ASSERT(root);
  return StmtCounter::run(root);
}
}  // namespace irpass::analysis

}  // namespace gstaichi::lang
