# C 语言编码规范与工程指引

本文档定义 C 语言项目的编码规范与质量要求。同时在第 10 节包含**嵌入式系统与裸机/RTOS 开发专有附则**。

---

## 1. 命名与代码风格

| 类别 | 规则 | 示例 | 说明 |
| :--- | :--- | :--- | :--- |
| **类型定义** | `PascalCase` | `QueueContext`, `HalUartDevice` | `typedef struct` 或 `typedef enum` |
| **函数命名** | `snake_case` | `uart_transmit_bytes()`, `queue_pop()` | 推荐以 `模块名_动词_对象` 形式前缀 |
| **变量命名** | `snake_case` | `buffer_len`, `retry_count` | 含义清晰，禁止无意义缩写 |
| **常量与宏** | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT`, `UART_BAUD_115200` | 宏与枚举常量 |
| **私有静态** | `snake_case` (前缀可加 `prv_` 或模块名) | `static int parse_header(...)` | 仅在当前编译单元可见的函数/变量必须用 `static` |

---

## 2. 头文件与模块划分

- **C-HDR-01 [MUST]**: 头文件必须包含防重复包含宏卫士（Header Guard）或编译器支持的 `#pragma once`。推荐采用基于路径的宏名，如 `MODULE_NAME_H_`。
- **C-HDR-02 [MUST]**: 头文件只包含其接口直接依赖的头文件，避免无节制地在头文件中包含大型系统头文件。
- **C-HDR-03 [MUST]**: 严禁在头文件中定义非 `inline` 的函数体或分配全局变量实体（全局变量应在头文件中使用 `extern` 声明，并在单个 `.c` 中定义）。
- **C-HDR-04 [SHOULD]**: 外部引用的 C 头文件应包含 `extern "C"` 包装块，以确保与 C++ 链接兼容：
  ```c
  #ifdef __cplusplus
  extern "C" {
  #endif

  /* declarations */

  #ifdef __cplusplus
  }
  #endif
  ```

---

## 3. 类型与数据表示

- **C-TYP-01 [MUST]**: 凡涉及特定位宽的数据，必须使用 `<stdint.h>` 和 `<stdbool.h>` 中定义的标准固定位宽类型（如 `uint8_t`, `int32_t`, `uint32_t`, `bool`），严禁在跨平台/底层代码中随意使用平台相关的裸 `int`, `long`, `short`。
- **C-TYP-02 [MUST]**: 对浮点数使用需审慎。在无硬件 FPU 或高精度要求的场景下，应使用定点数（Fixed Point）替代。
- **C-TYP-03 [MUST]**: 显式类型转换（Cast）应严格受控，禁止对结构体指针进行非法的严格别名转换（Strict Aliasing Violation）。

---

## 4. 指针、数组与内存安全

- **C-PTR-01 [MUST]**: 指针使用前必须确保有效性，对外暴露的 API 在解引用指针参数前必须检查 `NULL`（或通过断言明确前置条件）。
- **C-PTR-02 [MUST]**: 字符串操作严禁使用不带长度检查的不安全标准库函数（禁止使用 `strcpy`, `strcat`, `sprintf`, `gets`），必须使用边界安全的替代实现（如 `snprintf`, `strncpy` 并手动封顶 `\0`）。
- **C-PTR-03 [MUST]**: 遵循 Const-Correctness：凡函数内部不修改的输入指针参数，一律声明为 `const Type *`。
- **C-PTR-04 [MUST]**: 局部变量（尤其是指针与数组）必须显式初始化或在声明后立即明确赋初值，禁止读取未初始化的局部变量。

---

## 5. 错误处理与返回值

- **C-ERR-01 [MUST]**: 函数执行结果必须有明确的返回状态表达。通常遵循惯用法：
  - 成功返回 `0` 或 `STATUS_OK`，失败返回负数或具体错误枚举码（如 `-EINVAL`, `-EBUSY`）。
  - 或者指针类函数失败时明确返回 `NULL`。
- **C-ERR-02 [MUST]**: 调用任何可能失败的函数时，必须检查其返回值，严禁静默丢弃返回码（若有意忽略极少数无害函数如 `(void)printf(...)`，需显式强转 `(void)`）。
- **C-ERR-03 [SHOULD]**: 资源释放与集中清理推荐采用单入口单出口或 `goto cleanup` 结构化跳转范式，避免深层嵌套与遗漏释放：
  ```c
  int status = -1;
  void *buf = malloc(len);
  if (!buf) {
      return -ENOMEM;
  }

  if (step1() != 0) goto cleanup;
  if (step2() != 0) goto cleanup;

  status = 0; /* success */

  cleanup:
      free(buf);
      return status;
  ```

---

## 6. 宏与预处理器

- **C-MAC-01 [MUST]**: 宏定义必须为每个参数以及宏整体外层加上括号，防止操作符优先级混淆：
  ```c
  #define CLAMP(x, low, high) (((x) < (low)) ? (low) : (((x) > (high)) ? (high) : (x)))
  ```
- **C-MAC-02 [MUST]**: 复合语句宏必须使用 `do { ... } while (0)` 结构包裹，确保在 `if-else` 分支中能作为单条语句安全展开。
- **C-MAC-03 [SHOULD]**: 优先使用 `const` 变量、`enum` 或 `static inline` 函数替代功能复杂的宏，以保留类型检查和调试符号。

---

## 7. 初始化与资源生命周期

- **C-LIF-01 [MUST]**: 模块级资源应具备成对的生命周期管理函数，命名统一规范，例如 `module_init(...)` 和 `module_deinit(...)`。
- **C-LIF-02 [MUST]**: 动态分配的内存或句柄，释放后必须立即将指针置为 `NULL`，防止悬挂指针（Dangling Pointer）与二次释放（Double Free）。

---

## 8. 并发、共享状态与硬件寄存器

- **C-CON-01 [MUST]**: 被硬件寄存器映射、异步中断服务程序（ISR）修改、或与其他线程并发访问但未受互斥量保护的变量，必须修饰为 `volatile`，防止编译器激进优化造成读取陈旧值。
- **C-CON-02 [MUST]**: 访问主循环与 ISR 之间的共享数据结构时，必须进入临界区（关中断或使用原子操作），并在退出时立即恢复中断状态。
- **C-CON-03 [MUST]**: 在存在乱序执行或外设 DMA 传输的架构上，必须合理插入内存屏障（Memory Barrier / DMB / DSB）。

---

## 9. 平台相关代码与隔离

- **C-PLT-01 [MUST]**: 架构与平台相关代码（硬件外设驱动、寄存器映射、特定编译器属性如 `__attribute__((packed))`）必须通过硬件抽象层（HAL）与上层业务逻辑清晰隔离，禁止平台细节污染通用业务代码。
- **C-PLT-02 [SHOULD]**: 条件编译宏（如 `#if defined(CONFIG_ARCH_ARM)`）应集中在适配层，不应零散分布在业务流中。

---

## 10. 嵌入式系统与裸机/RTOS 专有附则 (Embedded Addendum)

在资源受限系统（微控制器 MCU、裸机固件、RTOS 任务上下文）中，必须额外遵循以下约束：

- **EMB-01 [MUST] 严控动态内存分配**:
  在固件主业务循环或长期运行的关键任务中，原则上**严禁使用 `malloc` / `free`**。所有缓冲区、任务控制块、队列应在编译期进行静态分配（Static Allocation），彻底消除内存碎片与运行时 OOM 风险。
- **EMB-02 [MUST] 中断服务程序 (ISR) 极速返回**:
  ISR 内部必须尽可能简短，只做必要的状态读取、标志位置位或关键数据入队。严禁在 ISR 中执行阻塞等待、耗时循环、复杂的浮点运算或调用可能发生上下文切换的 RTOS API。
- **EMB-03 [MUST] 栈深度可控与防御栈溢出**:
  嵌入式任务栈空间有限（通常为几百字节至几 KB）。严禁在函数栈上分配大型局部数组（如 `uint8_t temp[2048]`），严禁使用递归调用。关键系统应开启栈溢出检测（Stack Canary / RTOS Stack Watermark）。
- **EMB-04 [MUST] 硬件寄存器访问语义清晰**:
  操作外设寄存器时应使用清晰的位掩码（Bitmask）与位移操作，明确读-改-写（Read-Modify-Write）原子性，避免对只写寄存器进行读操作或对只读寄存器误写。

---

## 11. 自动化工具链配置

- **格式化**: 采用统一的 `.clang-format`（基于 LLVM 风格，缩进 4 格空格，行宽 100/120 字符）。可通过项目私有的 `.clang-format.override` 进行微调。
- **静态分析候选**:
  - `clang-tidy`: 检测潜在空指针解引用、未初始化变量、类型转换问题。
  - `cppcheck`: 专用于检测 C 内存泄露、越界访问及未定义行为。
