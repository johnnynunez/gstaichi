#include "taichi/program/callable.h"
#include "taichi/ir/type.h"
#include "taichi/program/program.h"

namespace taichi::lang {

Callable::Callable() = default;

Callable::~Callable() = default;

std::vector<int> Callable::insert_scalar_param(const DataType &dt,
                                               const std::string &name) {
  auto p = Parameter(dt->get_compute_type(), /*is_array=*/false);
  p.name = name;
  p.ptype = ParameterType::kScalar;
  return add_parameter(p);
}

int Callable::insert_ret(const DataType &dt) {
  rets.emplace_back(dt->get_compute_type());
  return (int)rets.size() - 1;
}

std::vector<int> Callable::insert_arr_param(const DataType &dt,
                                            int total_dim,
                                            std::vector<int> element_shape,
                                            const std::string &name) {
  auto p = Parameter(dt->get_compute_type(), /*is_array=*/true, 0,
                     total_dim, element_shape);
  p.name = name;
  return add_parameter(p);
}

std::vector<int> Callable::insert_ndarray_param(const DataType &dt,
                                                int ndim,
                                                const std::string &name,
                                                bool needs_grad) {
  // Transform ndarray param to a struct type with a pointer to `dt`.
  std::vector<int> element_shape{};
  auto dtype = dt;
  if (dt->is<TensorType>()) {
    element_shape = dt->as<TensorType>()->get_shape();
    dtype = dt->as<TensorType>()->get_element_type();
  }
  // FIXME: we have to use dtype here to scalarization.
  // If we could avoid using parameter_list in codegen it'll be fine
  auto *type = TypeFactory::get_instance().get_ndarray_struct_type(dtype, ndim,
                                                                   needs_grad);
  auto p =
      Parameter(type, /*is_array=*/true, 0, ndim + element_shape.size(),
                element_shape, BufferFormat::unknown, needs_grad);
  p.name = name;
  p.ptype = ParameterType::kNdarray;
  return add_parameter(p);
}

std::vector<int> Callable::insert_texture_param(int total_dim,
                                                const std::string &name) {
  // FIXME: we shouldn't abuse is_array for texture parameters
  // FIXME: using rwtexture struct type for texture parameters because C-API
  // does not distinguish between texture and rwtexture.
  auto *type = TypeFactory::get_instance().get_rwtexture_struct_type();
  auto p = Parameter(type, /*is_array=*/true, 0, total_dim,
                     std::vector<int>{});
  p.name = name;
  p.ptype = ParameterType::kTexture;
  return add_parameter(p);
}

std::vector<int> Callable::insert_pointer_param(const DataType &dt,
                                                const std::string &name) {
  auto p = Parameter(dt->get_compute_type(), /*is_array=*/true);
  p.name = name;
  return add_parameter(p);
}

std::vector<int> Callable::insert_rw_texture_param(int total_dim,
                                                   BufferFormat format,
                                                   const std::string &name) {
  // FIXME: we shouldn't abuse is_array for texture parameters
  auto *type = TypeFactory::get_instance().get_rwtexture_struct_type();
  auto p = Parameter(type, /*is_array=*/true, 0, total_dim,
                     std::vector<int>{}, format);
  p.name = name;
  p.ptype = ParameterType::kRWTexture;
  return add_parameter(p);
}

std::vector<int> Callable::add_parameter(const Parameter &param) {
  parameter_list.push_back(param);
  auto indices = std::vector<int>{(int)parameter_list.size() - 1};
  nested_parameters[indices] = param;
  return indices;
}

void Callable::finalize_rets() {
  std::vector<AbstractDictionaryMember> members;
  members.reserve(rets.size());
  for (int i = 0; i < rets.size(); i++) {
    members.push_back({rets[i].dt, fmt::format("ret_{}", i)});
  }
  auto *type =
      TypeFactory::get_instance().get_struct_type(members)->as<StructType>();
  std::string layout = program->get_kernel_return_data_layout();
  std::tie(ret_type, ret_size) =
      program->get_struct_type_with_data_layout(type, layout);
}

void Callable::finalize_params() {
  std::vector<AbstractDictionaryMember> members;
  members.reserve(parameter_list.size());
  for (int i = 0; i < parameter_list.size(); i++) {
    auto &param = parameter_list[i];
    members.push_back(
        {param.is_array && !param.get_dtype()->is<StructType>()
             ? TypeFactory::get_instance().get_pointer_type(param.get_dtype())
             : (const Type *)param.get_dtype(),
         fmt::format("arg_{}", i)});
  }
  auto *type =
      TypeFactory::get_instance().get_struct_type(members)->as<StructType>();
  std::string layout = program->get_kernel_argument_data_layout();
  std::tie(args_type, args_size) =
      program->get_struct_type_with_data_layout(type, layout);
}
}  // namespace taichi::lang
