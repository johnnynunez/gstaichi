#pragma once
#ifndef GSTAICHI_H
#define GSTAICHI_H

#include "gstaichi_platform.h"

#include "gstaichi_core.h"

#ifdef TI_WITH_VULKAN
#include "gstaichi_vulkan.h"
#endif  // TI_WITH_VULKAN

#ifdef TI_WITH_OPENGL
#include "gstaichi_opengl.h"
#endif  // TI_WITH_OPENGL

#ifdef TI_WITH_CUDA
#include "gstaichi_cuda.h"
#endif  // TI_WITH_CUDA

#ifdef TI_WITH_CPU
#include "gstaichi_cpu.h"
#endif  // TI_WITH_CPU

#ifdef TI_WITH_METAL
#include "gstaichi_metal.h"
#endif  // TI_WITH_METAL

#endif  // GSTAICHI_H
