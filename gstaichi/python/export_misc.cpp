/*******************************************************************************
    Copyright (c) The GsTaichi Authors (2016- ). All Rights Reserved.
    The use of this software is governed by the LICENSE file.
*******************************************************************************/

#include "gstaichi/rhi/metal/metal_api.h"
#include "gstaichi/runtime/gfx/runtime.h"
#include "gstaichi/common/core.h"
#include "gstaichi/common/interface.h"
#include "gstaichi/common/task.h"
#include "gstaichi/math/math.h"
#include "gstaichi/platform/cuda/detect_cuda.h"
#include "gstaichi/program/py_print_buffer.h"
#include "gstaichi/python/exception.h"
#include "gstaichi/python/export.h"
#include "gstaichi/python/memory_usage_monitor.h"
#include "gstaichi/system/benchmark.h"
#include "gstaichi/system/hacked_signal_handler.h"
#include "gstaichi/system/profiler.h"
#if defined(TI_WITH_CUDA)
#include "gstaichi/rhi/cuda/cuda_driver.h"
#endif

#include "gstaichi/platform/amdgpu/detect_amdgpu.h"
#if defined(TI_WITH_AMDGPU)
#include "gstaichi/rhi/amdgpu/amdgpu_driver.h"
#endif

#ifdef TI_WITH_VULKAN
#include "gstaichi/rhi/vulkan/vulkan_loader.h"
#endif

namespace gstaichi {

void test_raise_error() {
  raise_assertion_failure_in_python("Just a test.");
}

void print_all_units() {
  std::vector<std::string> names;
  auto interfaces = InterfaceHolder::get_instance()->interfaces;
  for (auto &kv : interfaces) {
    names.push_back(kv.first);
  }
  std::sort(names.begin(), names.end());
  int all_units = 0;
  for (auto &interface_name : names) {
    auto impls = interfaces[interface_name]->get_implementation_names();
    std::cout << " * " << interface_name << " [" << int(impls.size()) << "]"
              << std::endl;
    all_units += int(impls.size());
    std::sort(impls.begin(), impls.end());
    for (auto &impl : impls) {
      std::cout << "   + " << impl << std::endl;
    }
  }
  std::cout << all_units << " units in all." << std::endl;
}

void export_misc(py::module &m) {
  py::class_<Config>(m, "Config");  // NOLINT(bugprone-unused-raii)
  py::register_exception_translator([](std::exception_ptr p) {
    try {
      if (p)
        std::rethrow_exception(p);
    } catch (const ExceptionForPython &e) {
      PyErr_SetString(PyExc_RuntimeError, e.what());
    }
  });

  py::class_<Task, std::shared_ptr<Task>>(m, "Task")
      .def("initialize", &Task::initialize)
      .def("run",
           static_cast<std::string (Task::*)(const std::vector<std::string> &)>(
               &Task::run));

  py::class_<Benchmark, std::shared_ptr<Benchmark>>(m, "Benchmark")
      .def("run", &Benchmark::run)
      .def("test", &Benchmark::test)
      .def("initialize", &Benchmark::initialize);

#define TI_EXPORT_LOGGING(X)                 \
  m.def(#X, [](const std::string &msg) {     \
    gstaichi::Logger::get_instance().X(msg); \
  });

  m.def("flush_log", []() { gstaichi::Logger::get_instance().flush(); });

  TI_EXPORT_LOGGING(trace);
  TI_EXPORT_LOGGING(debug);
  TI_EXPORT_LOGGING(info);
  TI_EXPORT_LOGGING(warn);
  TI_EXPORT_LOGGING(error);
  TI_EXPORT_LOGGING(critical);

  m.def("print_all_units", print_all_units);
  m.def("set_core_state_python_imported", CoreState::set_python_imported);
  m.def("set_logging_level", [](const std::string &level) {
    Logger::get_instance().set_level(level);
  });
  m.def("logging_effective", [](const std::string &level) {
    return Logger::get_instance().is_level_effective(level);
  });
  m.def("set_logging_level_default",
        []() { Logger::get_instance().set_level_default(); });
  m.def("set_core_trigger_gdb_when_crash",
        CoreState::set_trigger_gdb_when_crash);
  m.def("test_raise_error", test_raise_error);
  m.def("get_default_float_size", []() { return sizeof(real); });
  m.def("trigger_sig_fpe", []() {
    int a = 2;
    a -= 2;
    return 1 / a;
  });
  m.def("print_profile_info",
        [&]() { Profiling::get_instance().print_profile_info(); });
  m.def("clear_profile_info",
        [&]() { Profiling::get_instance().clear_profile_info(); });
  m.def("start_memory_monitoring", start_memory_monitoring);
  m.def("get_repo_dir", get_repo_dir);
  m.def("get_python_package_dir", get_python_package_dir);
  m.def("set_python_package_dir", set_python_package_dir);
  m.def("cuda_version", get_cuda_version_string);
  m.def("test_cpp_exception", [] {
    try {
      throw std::exception();
    } catch (const std::exception &e) {
      printf("caught.\n");
    }
    printf("test was successful.\n");
  });
  m.def("pop_python_print_buffer", []() { return py_cout.pop_content(); });
  m.def("toggle_python_print_buffer", [](bool opt) { py_cout.enabled = opt; });
  m.def("with_cuda", is_cuda_api_available);
  m.def("with_amdgpu", is_rocm_api_available);
#ifdef TI_WITH_METAL
  m.def("with_metal", gstaichi::lang::metal::is_metal_api_available);
#else
  m.def("with_metal", []() { return false; });
#endif
#ifdef TI_WITH_VULKAN
  m.def("with_vulkan", gstaichi::lang::vulkan::is_vulkan_api_available);
  m.def("set_vulkan_visible_device",
        gstaichi::lang::vulkan::set_vulkan_visible_device);
#else
  m.def("with_vulkan", []() { return false; });
#endif

  py::class_<HackedSignalRegister>(m, "HackedSignalRegister").def(py::init<>());
}

}  // namespace gstaichi
