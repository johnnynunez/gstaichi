# Compound types overview

The following compound types are available:
- `@ti.struct`
- `@ti.dataclass` (effectively an alias of `@ti.struct`: uses same underlying class, and mechanism)
- `@ti.data_oriented`
- `argpack`
- `dataclasses.dataclass`

| type                               | can be passed to ti.kernel? | can be passed to ti.func? | can contain ndarray? | can contain field? | can be mixed with other parameters? | supports differentiation? | can be nested? | caches arguments? | comments |
|------------------------------------|-----------------------------|---------------------------|----------------------|--------------------|-------------------------------------|---------------------------|----------------|-------------------|----------|
| `@ti.struct`, `@ti.dataclass`      |                         yes | yes                       |                   no |                yes | yes                                 | yes                       | yes            | no                |          |
| `@ti.data_oriented`                |yes                          | yes                       | no                   |  yes               |yes                                   | yes                       | no             | no                |          |
| `ti.argpack`                          |yes                          | no                        | yes                  | no                 | no                                   | yes                      | yes            | yes               | scheduled to be removed |
| `@dataclasses.dataclass`            | yes                         | yes                       | yes                  | yes                | yes                                   | yes                     |planned         | no                | recommended approach |

`@dataclass.dataclass` is the current recommended approach:
- supports both fields and ndarrays
- planned to be nestable
- can be used in both kernel and func calls
- can be combined with other parameters, in a kernel or func call

ti.argpack is scheduled to be removed because its functionality is a subset of the union of `dataclasses.dataclass` and caching (planned).
