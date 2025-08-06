// Note that TI_ASSERT provided by runtime doesn't check fail immediately. As
// a hack, we just check the last error code whenever we call TI_ASSERT.
#define TI_TEST_CHECK(cond, r)                               \
  do {                                                       \
    TI_ASSERT(cond);                                         \
    if ((r)->error_code) {                                   \
      gstaichi_printf((r), "%s", (r)->error_message_template); \
      abort();                                               \
    }                                                        \
  } while (0)

#define ATOMIC_INSERT(T)                                                  \
  do {                                                                    \
    auto base_ptr = reinterpret_cast<int##T *>(base_ptr_);                \
    int##T *num_triplets = base_ptr;                                      \
    auto data_base_ptr = base_ptr + 1;                                    \
    auto triplet_id = atomic_add_i##T(num_triplets, 1);                   \
    data_base_ptr[triplet_id * 3] = i;                                    \
    data_base_ptr[triplet_id * 3 + 1] = j;                                \
    data_base_ptr[triplet_id * 3 + 2] = gstaichi_union_cast<int##T>(value); \
  } while (0);

i32 do_nothing(RuntimeContext *context) {
  return 0;
}

i32 refresh_counter(RuntimeContext *context) {
  return 0;
}

i32 insert_triplet_f32(RuntimeContext *context,
                       int64 base_ptr_,
                       int i,
                       int j,
                       float value) {
  ATOMIC_INSERT(32);
  return 0;
}

i32 insert_triplet_f64(RuntimeContext *context,
                       int64 base_ptr_,
                       int i,
                       int j,
                       float64 value) {
  ATOMIC_INSERT(64);
  return 0;
}

i32 test_internal_func_args(RuntimeContext *context,
                            float32 i,
                            float32 j,
                            int32 k) {
  return static_cast<int>((i + j) * k);
}

i32 test_stack(RuntimeContext *context) {
  auto stack = new u8[132];
  stack_push(stack, 16, 4);
  stack_push(stack, 16, 4);
  stack_push(stack, 16, 4);
  stack_push(stack, 16, 4);
  return 0;
}

i32 test_list_manager(RuntimeContext *context) {
  auto runtime = context->runtime;
  gstaichi_printf(runtime, "LLVMRuntime %p\n", runtime);
  auto list = context->runtime->create<ListManager>(runtime, 4, 16);
  for (int i = 0; i < 320; i++) {
    gstaichi_printf(runtime, "appending %d\n", i);
    auto j = i + 5;
    list->append(&j);
  }
  for (int i = 0; i < 320; i++) {
    TI_TEST_CHECK(list->get<i32>(i) == i + 5, runtime);
  }
  return 0;
}

i32 test_node_allocator(RuntimeContext *context) {
  auto runtime = context->runtime;
  gstaichi_printf(runtime, "LLVMRuntime %p\n", runtime);
  auto nodes = context->runtime->create<NodeManager>(runtime, sizeof(i64), 4);
  Ptr ptrs[24];
  for (int i = 0; i < 19; i++) {
    gstaichi_printf(runtime, "allocating %d\n", i);
    ptrs[i] = nodes->allocate();
    gstaichi_printf(runtime, "ptr %p\n", ptrs[i]);
  }
  for (int i = 0; i < 5; i++) {
    gstaichi_printf(runtime, "deallocating %d\n", i);
    gstaichi_printf(runtime, "ptr %p\n", ptrs[i]);
    nodes->recycle(ptrs[i]);
  }
  nodes->gc_serial();
  for (int i = 19; i < 24; i++) {
    gstaichi_printf(runtime, "allocating %d\n", i);
    ptrs[i] = nodes->allocate();
  }
  for (int i = 5; i < 19; i++) {
    TI_TEST_CHECK(nodes->locate(ptrs[i]) == i, runtime);
  }

  for (int i = 19; i < 24; i++) {
    auto idx = nodes->locate(ptrs[i]);
    gstaichi_printf(runtime, "i %d", i);
    gstaichi_printf(runtime, "idx %d", idx);
    TI_TEST_CHECK(idx == i - 19, runtime);
  }
  return 0;
}

i32 test_node_allocator_gc_cpu(RuntimeContext *context) {
  auto runtime = context->runtime;
  gstaichi_printf(runtime, "LLVMRuntime %p\n", runtime);
  auto nodes = context->runtime->create<NodeManager>(runtime, sizeof(i64), 4);
  constexpr int kN = 24;
  constexpr int kHalfN = kN / 2;
  Ptr ptrs[kN];
  // Initially |free_list| is empty
  TI_TEST_CHECK(nodes->free_list->size() == 0, runtime);
  for (int i = 0; i < kN; i++) {
    gstaichi_printf(runtime, "[1] allocating %d\n", i);
    ptrs[i] = nodes->allocate();
    gstaichi_printf(runtime, "[1] ptr %p\n", ptrs[i]);
  }
  for (int i = 0; i < kN; i++) {
    gstaichi_printf(runtime, "[1] deallocating %d\n", i);
    gstaichi_printf(runtime, "[1] ptr %p\n", ptrs[i]);
    nodes->recycle(ptrs[i]);
  }
  TI_TEST_CHECK(nodes->free_list->size() == 0, runtime);
  nodes->gc_serial();
  // After the first round GC, |free_list| should have |kN| items.
  TI_TEST_CHECK(nodes->free_list->size() == kN, runtime);

  // In the second round, all items should come from |free_list|.
  for (int i = 0; i < kHalfN; i++) {
    gstaichi_printf(runtime, "[2] allocating %d\n", i);
    ptrs[i] = nodes->allocate();
    gstaichi_printf(runtime, "[2] ptr %p\n", ptrs[i]);
  }
  TI_TEST_CHECK(nodes->free_list_used == kHalfN, runtime);
  for (int i = 0; i < kHalfN; i++) {
    gstaichi_printf(runtime, "[2] deallocating %d\n", i);
    gstaichi_printf(runtime, "[2] ptr %p\n", ptrs[i]);
    nodes->recycle(ptrs[i]);
  }
  nodes->gc_serial();
  // After GC, all items should be returned to |free_list|.
  gstaichi_printf(runtime, "free_list_size=%d\n", nodes->free_list->size());
  TI_TEST_CHECK(nodes->free_list->size() == kN, runtime);

  return 0;
}

i32 test_active_mask(RuntimeContext *context) {
  auto rt = context->runtime;
  gstaichi_printf(rt, "%d activemask %x\n", thread_idx(), cuda_active_mask());

  auto active_mask = cuda_active_mask();
  auto remaining = active_mask;
  while (remaining) {
    auto leader = cttz_i32(remaining);
    gstaichi_printf(rt, "current leader %d bid %d tid %d\n", leader, block_idx(),
                  thread_idx());
    warp_barrier(active_mask);
    remaining &= ~(1u << leader);
  }

  return 0;
}

i32 test_shfl(RuntimeContext *context) {
  auto rt = context->runtime;
  auto s =
      cuda_shfl_down_sync_i32(cuda_active_mask(), warp_idx() + 1000, 2, 31);
  gstaichi_printf(rt, "tid %d tid_shfl %d\n", thread_idx(), s);

  return 0;
}

#undef TI_TEST_CHECK
