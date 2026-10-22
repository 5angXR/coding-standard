# 通用工程原则与编码基线 (General Engineering Principles)

本文档定义跨语言(C, Rust, Python 等)通用的软件工程与编码质量基线. 所有接入本规范的项目均应遵循本准则.

## 1. 规范级别定义 (RFC 2119)

- **MUST (强制)**: 绝对要求, 违背此规则的代码不得通过评审与合并.
- **SHOULD (推荐)**: 强烈推荐, 除非有被明确论证且记录在案的技术理由, 否则必须遵守.
- **MAY (可选)**: 建议或可选做法, 由项目团队根据具体场景自行权衡.

---

## 2. 核心工程原则

### 2.1 命名与清晰性

| ID | 规则描述 | 级别 | 适用范围 | 检查方式 |
| :--- | :--- | :--- | :--- | :--- |
| **GEN-NAM-01** | 标识符命名必须准确表达其业务含义或技术职责, 禁止使用单字母(循环计数 `i`, `j` 除外)或无意义拼音缩写. | **MUST** | 全语言 | Code Review |
| **GEN-NAM-02** | 遵循所在语言的命名习惯(C/Rust 函数与变量使用 `snake_case`, 类型与结构体使用 `PascalCase`; Python 类使用 `PascalCase`, 函数变量使用 `snake_case`; 常量使用 `UPPER_SNAKE_CASE`). | **MUST** | 全语言 | Linter / Review |
| **GEN-NAM-03** | 布尔类型变量与函数应具有明确的是非语义, 推荐以 `is_`, `has_`, `can_`, `should_` 开头. | **SHOULD** | 全语言 | Code Review |
| **GEN-NAM-04** | 遇到常见可缩写词汇时, 函数与变量命名应采用统一的标准缩写(如 `button` -> `btn`, `count` -> `cnt`, `event` -> `evt`, `buffer` -> `buf`, `length` -> `len`, `config` -> `cfg`, `message` -> `msg`, `context` -> `ctx`, `device` -> `dev`, `number` -> `num`, `pointer` -> `ptr`, `string` -> `str`, `value` -> `val`, `initialize` -> `init`, `calculate` -> `calc`, `arguments` -> `args` 等), 禁止自创生僻缩写或同一词汇在同一模块中全拼与缩写混用. | **SHOULD** | 全语言 | typos / Review |

### 2.2 复杂度与函数职责

| ID | 规则描述 | 级别 | 适用范围 | 检查方式 |
| :--- | :--- | :--- | :--- | :--- |
| **GEN-CMP-01** | 单个函数应恪守单一职责原则(SRP). 避免"上帝函数"或混杂不同层级抽象的操作. | **MUST** | 全语言 | Code Review |
| **GEN-CMP-02** | 函数物理行数建议控制在 80 行以内, 圈复杂度(Cyclomatic Complexity)控制在 15 以内. 超出时应进行合理拆分. | **SHOULD** | 全语言 | Linter / Review |
| **GEN-CMP-03** | 避免无意义的过度设计与过早抽象. 优先编写清晰, 扁平的代码, 只在出现 3 次以上重复或存在明确多态演进需求时才引入抽象层. | **SHOULD** | 全语言 | Code Review |

### 2.3 错误处理与防御性设计

| ID | 规则描述 | 级别 | 适用范围 | 检查方式 |
| :--- | :--- | :--- | :--- | :--- |
| **GEN-ERR-01** | 所有可能的失败路径必须显式处理, 严禁静默吞掉错误或在无防护前提下假设操作一定成功(如未校验返回码, 未处理异常, 未检查 `Result`/`Option`). | **MUST** | 全语言 | Static Analysis / Review |
| **GEN-ERR-02** | 向上层抛出或返回错误时, 必须保留足够的诊断上下文(错误发生位置, 关键参数, 根本原因), 禁止只返回空或模糊错误. | **SHOULD** | 全语言 | Code Review |
| **GEN-ERR-03** | 在不可恢复或严重逻辑破损状态下, 应采取确定性策略终止或降级, 严禁让系统处于未定义的脏状态继续运行. | **MUST** | 全语言 | Code Review |

### 2.4 资源生命周期与状态管理

| ID | 规则描述 | 级别 | 适用范围 | 检查方式 |
| :--- | :--- | :--- | :--- | :--- |
| **GEN-RES-01** | 所有系统资源(内存堆, 文件描述符, 网络 Socket, 互斥锁, 硬件外设句柄)必须有清晰明确的所有权和生命周期定义. | **MUST** | 全语言 | Sanitizer / Review |
| **GEN-RES-02** | 优先利用语言内置的 RAII 机制(C++ / Rust)或上下文管理器 `with`(Python)管理资源生命周期; C 语言必须遵循成对的 `init`/`deinit` 或 `open`/`close` 约定. | **MUST** | 全语言 | Code Review |
| **GEN-RES-03** | 限制全局可变状态(Global Mutable State). 若必须使用全局变量或单例, 必须在文档中明确注明其并发访问约束与重入安全性. | **SHOULD** | 全语言 | Code Review |

### 2.5 注释与文档

| ID | 规则描述 | 级别 | 适用范围 | 检查方式 |
| :--- | :--- | :--- | :--- | :--- |
| **GEN-DOC-01** | 注释重点解释**"为什么这样做 (Why)"**, 约束条件, 潜在副作用和非显而易见的技术权衡, 而不是复述代码本身做了什么 (What). | **MUST** | 全语言 | Code Review |
| **GEN-DOC-02** | 公开 API, 公共结构体与模块导出项必须提供规范的接口文档(参数含义, 返回值, 可能返回的错误, 前置条件与调用约定). | **MUST** | 全语言 | DocGen / Review |
| **GEN-DOC-03** | 代码中存在已知妥协或临时方案时, 必须标记 `TODO(username)` 或 `FIXME` 并附带跟踪 issue/说明, 严禁无名死注释. | **SHOULD** | 全语言 | Linter / Grep |
| **GEN-DOC-04** | 代码中的所有注释(包括行内注释, 块注释以及 docstring / doxygen 文档注释)必须使用英文书写, 确保跨团队与跨平台协作的通用性, 并防止非 ASCII 字符在不同编译环境下引发编码问题. | **MUST** | 全语言 | Code Review |

### 2.6 依赖可复现性与供应链安全

| ID | 规则描述 | 级别 | 适用范围 | 检查方式 |
| :--- | :--- | :--- | :--- | :--- |
| **GEN-DEP-01** | 生产项目必须使用确定性的依赖锁定机制(如 `Cargo.lock`,`poetry.lock`/`requirements.txt` 固定版本, 明确的 C 第三方源码 tag 或 submodule commit). | **MUST** | 全语言 | CI / Audit |
| **GEN-DEP-02** | 严禁引入许可证不合规或未经验证的边缘第三方依赖. 引入新依赖前应评估其维护活跃度, 代码体量与安全面. | **SHOULD** | 全语言 | Dependency Review |

### 2.7 自动化测试与可验证性

| ID | 规则描述 | 级别 | 适用范围 | 检查方式 |
| :--- | :--- | :--- | :--- | :--- |
| **GEN-TST-01** | 核心业务逻辑与算法必须具备自动化单元测试, 且需覆盖典型正向路径(Happy Path)与边界/异常分支(Error Path). | **MUST** | 全语言 | Test Suite in CI |
| **GEN-TST-02** | 测试用例必须具有确定性(Deterministic), 不应依赖不确定的外部网络请求, 当前墙上时钟或未初始化的随机种子. | **MUST** | 全语言 | CI Test Run |
| **GEN-TST-03** | 修复已发现的 Bug 时, 应当补充针对该场景的回归测试用例(Regression Test). | **SHOULD** | 全语言 | Code Review |

### 2.8 稳健性与可维护性优先

| ID | 规则描述 | 级别 | 适用范围 | 检查方式 |
| :--- | :--- | :--- | :--- | :--- |
| **GEN-MNT-01** | 在性能满足系统吞吐与延迟指标的前提下,**代码的正确性, 可读性, 可维护性与可调试性永远优先于"黑魔法"式的微优化或极端简短写法**. | **MUST** | 全语言 | Code Review |
| **GEN-MNT-02** | 任何性能优化必须基于真实的 Profiling / Benchmark 数据度量, 并保留基准测试用例与比对记录. | **SHOULD** | 全语言 | Benchmark Docs |
