#include "gtest/gtest.h"
#include "gstaichi/ir/ir_builder.h"
#include "gstaichi/ir/statements.h"
#include "gstaichi/inc/constants.h"
#include "gstaichi/program/program.h"
#include "tests/cpp/program/test_program.h"
#include "gstaichi/aot/graph_data.h"
#include "tests/cpp/ir/ndarray_kernel.h"
#include "gstaichi/program/graph_builder.h"
#ifdef TI_WITH_VULKAN
#include "gstaichi/rhi/vulkan/vulkan_loader.h"
#endif

using namespace gstaichi;
using namespace lang;
#ifdef TI_WITH_VULKAN
TEST(GraphTest, SimpleGraphRun) {
  // Otherwise will segfault on macOS VM,
  // where Vulkan is installed but no devices are present
  if (!vulkan::is_vulkan_api_available()) {
    return;
  }
  TestProgram test_prog;
  test_prog.setup(Arch::vulkan);

  const int size = 10;

  auto ker1 = setup_kernel1(test_prog.prog());
  auto ker2 = setup_kernel2(test_prog.prog());

  auto g_builder = std::make_unique<GraphBuilder>();
  auto seq = g_builder->seq();
  auto arr_arg = aot::Arg{aot::ArgKind::kNdarray, "arr", PrimitiveType::i32, 1};
  seq->dispatch(ker1.get(), {arr_arg});
  seq->dispatch(ker2.get(), {arr_arg, aot::Arg{
                                          aot::ArgKind::kScalar,
                                          "x",
                                          PrimitiveType::i32,
                                      }});

  auto g = g_builder->compile();

  auto array = Ndarray(test_prog.prog(), PrimitiveType::i32, {size});
  array.write_int({0}, 2);
  array.write_int({2}, 40);
  std::unordered_map<std::string, aot::IValue> args;
  args.insert({"arr", aot::IValue::create(array)});
  args.insert({"x", aot::IValue::create<int>(2)});

  g->jit_run(test_prog.prog()->compile_config(), args);
  test_prog.prog()->synchronize();
  EXPECT_EQ(array.read_int({0}), 2);
  EXPECT_EQ(array.read_int({1}), 2);
  EXPECT_EQ(array.read_int({2}), 42);
}
#endif
