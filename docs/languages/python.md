# Python 语言编码规范与工程指引

本文档定义现代 Python（基线 Python 3.10+）工程规范，基于 PEP 8，使用现代快速工具链 Ruff 提供自动化校验与格式化支持。

---

## 1. 命名与代码风格

| 类别 | 规范格式 | 示例 | 说明 |
| :--- | :--- | :--- | :--- |
| **模块 / 包名** | `snake_case` (短小简明，不含大写或短横线) | `data_cleaner`, `utils` | 保持简短易懂 |
| **类名 (Class)** | `PascalCase` | `ConfigParser`, `HttpRequestHandler` | 异常类通常以 `Error` 结尾 |
| **函数与方法** | `snake_case` | `parse_arguments()`, `calculate_hash()` | 动词或动宾结构 |
| **局部与实例变量** | `snake_case` | `total_count`, `retry_delay` | 避免使用易混淆字符 |
| **受保护成员** | 单下划线前缀 `_snake_case` | `_internal_cache`, `_prepare()` | 模块内部或类内部使用 |
| **私有混淆成员** | 双下划线前缀 `__snake_case` (审慎使用) | `__mangled_var` | 仅在避免子类命名冲突时使用 |
| **全局常量** | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT`, `MAX_RETRIES` | 模块级常量 |

---

## 2. 类型标注与现代语法特性 (Type Hints)

- **PY-TYP-01 [MUST]**: 核心公共模块、API 入口、关键数据模型与服务层函数的输入参数与返回值必须提供类型注解（Type Hints）。
- **PY-TYP-02 [MUST]**: 基于 Python 3.10+ 现代语法规范，优先使用内置泛型与联合类型：
  - 使用 `list[str]` 代替 `typing.List[str]`
  - 使用 `dict[str, int]` 代替 `typing.Dict[str, int]`
  - 使用 `int | None` 代替 `typing.Optional[int]`
  - 使用 `int | str` 代替 `typing.Union[int, str]`
- **PY-TYP-03 [SHOULD]**: 对于纯数据结构实体，优先使用 `dataclasses.dataclass(slots=True)` 或 Pydantic 模型，避免使用无类型约束的裸 `dict` 或长元组 `tuple`。

---

## 3. 错误处理与防御性设计

- **PY-ERR-01 [MUST]**: 严禁编写空的或捕获过于宽泛且未记录的 `except:` 或 `except Exception: pass`。如果必须捕获兜底异常，必须记录日志或详细堆栈：
  ```python
  # BAD
  try:
      do_something()
  except Exception:
      pass

  # GOOD
  try:
      do_something()
  except (KeyError, ValueError) as err:
      logger.warning("Invalid configuration value encountered: %s", err)
  ```
- **PY-ERR-02 [MUST]**: 在捕获并重新抛出自定义业务异常时，必须使用 `raise NewException(...) from err` 保留原始调用链上下文（Exception Chaining）。
- **PY-ERR-03 [SHOULD]**: 自定义异常应继承自项目的基础异常类（如 `AppBaseError`），且命名以 `Error` 结尾。

---

## 4. 资源生命周期与上下文管理

- **PY-RES-01 [MUST]**: 所有涉及外部资源（文件句柄、网络会话、数据库连接、临时目录、互斥锁）的操作必须使用 `with` 上下文管理器，确保发生异常时资源必然释放。
- **PY-RES-02 [MUST]**: 打开文本文件时必须显式指定字符编码 `encoding="utf-8"`，严禁依赖操作系统默认的平台编码。

---

## 5. 架构纯粹性与避免反模式

- **PY-ARC-01 [MUST]**: 模块导入严禁使用星号通配符导入（`from module import *`），必须显式导入具体符号或导入模块命名空间。
- **PY-ARC-02 [MUST]**: 严禁将可变对象（如列表 `[]`、字典 `{}`、对象实例）作为函数默认参数：
  ```python
  # BAD
  def append_to(item, target_list=[]):
      target_list.append(item)
      return target_list

  # GOOD
  def append_to(item, target_list: list[str] | None = None) -> list[str]:
      if target_list is None:
          target_list = []
      target_list.append(item)
      return target_list
  ```
- **PY-ARC-03 [SHOULD]**: 限制全局状态与模块顶层的副作用执行。模块在被 `import` 时不应直接执行阻塞式网络连接、重型文件读写或复杂的初始化。

---

## 6. 自动化工具链配置

- **基线工具**: 统一使用 Ruff（兼具格式化器与代码检查器能力）。
- **配置文件**: 本仓库提供独立的 `ruff.toml`（不强行修改既有 `pyproject.toml`）。
- **项目私有覆盖**: 项目若需微调，可通过 `extend = "ruff.base.toml"` 或在本地追加自身专属规则。
- **常用命令**:
  - 格式化检查: `ruff format --check .`
  - 静态检查: `ruff check .`
  - 自动修复: `ruff check --fix .`
