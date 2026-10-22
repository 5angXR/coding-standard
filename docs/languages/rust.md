# Rust 语言编码规范与工程指引

本文档定义 Rust 语言项目的工程规范, 基于 Rust 2021 Edition 及官方 API 设计准则(Rust API Guidelines).

---

## 1. 命名与惯用法

| 类别 | 规范格式 | 示例 |
| :--- | :--- | :--- |
| **包名 / Crate** | `snake_case` (禁止使用减号 `-` 与下划线混用) | `firmware_maker`, `protocol_parser` |
| **模块 / Module** | `snake_case` | `mod packet_builder;` |
| **类型 / Struct / Enum / Trait** | `PascalCase` | `DeviceState`, `FlashBlock`, `DisplayDriver` |
| **函数 / 方法** | `snake_case` | `calc_crc()`, `into_bytes()` |
| **局部变量 / 结构体字段** | `snake_case` | `chunk_size`, `dev_id`, `evt_cnt` |
| **常量 / 静态变量** | `UPPER_SNAKE_CASE` | `MAX_PAYLOAD_SIZE`, `DEFAULT_TIMEOUT_MS` |
| **类型参数 / 泛型** | 单个大写字母或简短 `PascalCase` | `T`, `E`, `Item`, `Buf: AsRef<[u8]>` |

转换类函数命名必须严格遵循惯用法:
- `as_foo(&self) -> &Foo`: 廉价借用转换(Borrow).
- `to_foo(&self) -> Foo`: 高开销或克隆转换(Clone/Allocation).
- `into_foo(self) -> Foo`: 消耗所有权的类型转换(Move/Conversion).

---

## 2. 类型系统与所有权

- **RS-TYP-01 [MUST]**: 优先利用 Rust 严格的静态类型系统将无效状态在编译期排除(Make Invalid States Unrepresentable), 避免使用布尔标志位组合表示复杂的互斥状态, 推荐使用 `enum` 携带具体数据.
- **RS-TYP-02 [MUST]**: 优先传递借用(`&str`, `&[u8]`, `&T`)而非无谓转移所有权, 严禁仅为了解决所有权借用检查器(Borrow Checker)报错而随意进行大对象的无脑 `.clone()`.
- **RS-TYP-03 [SHOULD]**: 接口参数设计应灵活, 接收切片或引用时优先使用泛型或解引用类型(如接收 `impl AsRef<Path>` 而不是 `&PathBuf`, 接收 `&[u8]` 而非 `&Vec<u8>`).
- **RS-TYP-04 [SHOULD]**: 保持生命周期参数(Lifetime)扁平化, 避免设计层级过深的多生命周期标记(如 `<'a, 'b, 'c>`), 复杂关系应重新审视所有权拓扑设计.

---

## 3. 错误处理与健壮性

- **RS-ERR-01 [MUST]**: 业务逻辑与生产库代码中严禁随意调用 `.unwrap()`.
- **RS-ERR-02 [MUST]**: 严禁在库代码中直接调用 `panic!()`,`unreachable!()`(除非已经从数学或前置校验上严格证明该分支绝对不可达, 并附带注释).
- **RS-ERR-03 [SHOULD]**: 如果必须使用 `.expect("reason")`, 错误描述必须陈述**"为何此处绝对不可能失败的前提假设"**(例如 `expect("mutex poisoned by previous thread crash")`), 而非仅仅复述错误本身.
- **RS-ERR-04 [MUST]**: 库级错误应定义专门的枚举错误类型(推荐使用 `thiserror`), 向上暴露精确的错误语义; 应用级可使用 `anyhow` 进行上下文包装.
- **RS-ERR-05 [MUST]**: 对 `Option` 和 `Result` 的处理应优先使用模式匹配, 组合子(`map`, `and_then`)或 `?` 操作符, 禁止将其简单当作 C 风格返回值来忽略.

---

## 4. Unsafe 代码防线与审计

- **RS-UNS-01 [MUST]**: 坚决限制 `unsafe` 的使用. 只有在直接与 FFI 交互, 操作硬件底层 MMIO 寄存器或经过严格基准测试证明的核心热点路径时, 才允许使用 `unsafe`.
- **RS-UNS-02 [MUST]**: 每一个 `unsafe` 代码块或函数必须紧随其后附带 `// SAFETY:` 注释, 详述调用前置条件, 不变性保证(Invariants)以及为什么此处是内存安全的.
  ```rust
  // SAFETY: `ptr` is guaranteed to be non-null and aligned because it was checked
  // at initialization, and `len` is within the allocated capacity.
  unsafe {
      std::slice::from_raw_parts(ptr, len)
  }
  ```
- **RS-UNS-03 [MUST]**: `unsafe` 代码必须被包裹在小范围, 安全抽象的外层 API 内部, 禁止将未经安全验证的裸指针直接暴露为公共安全接口.
- **RS-UNS-04 [MUST]**: 项目中若包含 `unsafe` 代码, 必须在 CI 中配置 Miri (`cargo miri test`) 验证未定义行为(UB).

---

## 5. 依赖管理与构建可复现性

- **RS-DEP-01 [MUST]**: 最终应用或二进制(Binary)必须将 `Cargo.lock` 纳入版本控制, 确保团队成员与 CI 构建产物 100% 可复现.
- **RS-DEP-02 [SHOULD]**: 审查 `Cargo.toml` 依赖引入, 避免引入体量庞大或递归依赖层级过深的冷门 crate. 关键基础设施应定期运行 `cargo audit`.

---

## 6. 自动化工具链配置

- **格式化**: 使用 `rustfmt.toml` 配置基线. 在 CI 中使用 `cargo fmt --check` 强制校验.
- **静态分析与代码异味**:
  - 在 CI 中运行 `cargo clippy -- -D warnings`, 严禁带着 Clippy 警告合并代码.
  - 核心项目建议配置 `#![deny(missing_docs)]` 约束公共 API 文档完备性.
- **私有微调**: 项目如需调整行宽(如 `max_width = 120`), 可在项目根目录下创建 `rustfmt.override.toml`, 由 `sync.py` 自动合并编译.
