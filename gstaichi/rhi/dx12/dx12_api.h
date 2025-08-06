#pragma once
#include "gstaichi/common/core.h"
#include "gstaichi/rhi/device.h"

#ifdef TI_WITH_DX12

#endif

namespace gstaichi::lang {
namespace directx12 {

bool is_dx12_api_available();

std::shared_ptr<Device> make_dx12_device();

std::vector<uint8_t> validate_and_sign(
    std::vector<uint8_t> &input_dxil_container);

}  // namespace directx12
}  // namespace gstaichi::lang
