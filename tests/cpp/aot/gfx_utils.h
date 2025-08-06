#pragma once
#include "gtest/gtest.h"

#include "gstaichi/rhi/device.h"
#include "gstaichi/aot/graph_data.h"
#include "gstaichi/program/graph_builder.h"
#include "gstaichi/program/program.h"

namespace gstaichi::lang {
namespace aot_test_utils {
[[maybe_unused]] static void write_devalloc(
    gstaichi::lang::DeviceAllocation &alloc,
    const void *data,
    size_t size);

[[maybe_unused]] static void
load_devalloc(gstaichi::lang::DeviceAllocation &alloc, void *data, size_t size);

void view_devalloc_as_ndarray(Device *device_);

[[maybe_unused]] void run_cgraph1(Arch arch, gstaichi::lang::Device *device_);

[[maybe_unused]] void run_cgraph2(Arch arch, gstaichi::lang::Device *device_);

[[maybe_unused]] void run_kernel_test1(Arch arch, gstaichi::lang::Device *device);

[[maybe_unused]] void run_kernel_test2(Arch arch, gstaichi::lang::Device *device);

[[maybe_unused]] void run_dense_field_kernel(Arch arch,
                                             gstaichi::lang::Device *device);

[[maybe_unused]] void run_mpm88_graph(Arch arch, gstaichi::lang::Device *device_);
}  // namespace aot_test_utils
}  // namespace gstaichi::lang
