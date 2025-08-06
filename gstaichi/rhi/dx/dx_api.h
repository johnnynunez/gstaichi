#pragma once
#include "gstaichi/common/core.h"
#include "gstaichi/rhi/device.h"

#ifdef TI_WITH_DX11
#pragma comment(lib, "d3d11.lib")
#pragma comment(lib, "d3dcompiler.lib")
#pragma comment(lib, "dxguid.lib")
#include <d3d11.h>
#endif

namespace gstaichi::lang {
namespace directx11 {

bool is_dx_api_available();

std::shared_ptr<Device> make_dx11_device();

}  // namespace directx11
}  // namespace gstaichi::lang
