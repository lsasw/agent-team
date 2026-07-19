# Python 学习问答录

> 在构建 agent-team 项目过程中遇到的 Python 语法疑问，按对话顺序整理。

---

## 1. 单下划线前缀 `_method` 是什么意思？

Python 中带一个下划线前缀的函数名（如 `_build_system_message`）是**约定俗成的"内部实现"标记**：

| 含义 | 说明 |
|------|------|
| **"私有"约定** | 告诉使用者："这是内部方法，别在外面调，以后可能随时改" |
| **无强制约束** | 不像双下划线 `__method` 会触发 name mangling，`_method` 纯靠自觉 |
| **import 行为** | `from module import *` 不会导入 `_` 前缀的名字 |

```python
# ✅ 外部使用者应该调这个
agent.run("任务")

# ⚠️ 内部 helper，外部不应直接调用
agent._build_system_message()
agent._parse_response(text)
```

这相当于 Python 世界的"受保护成员"——**约定大于配置**。

---

## 2. `__init__` 的参数和 `self.xxx` 属性为什么不一样多？

**参数**是调用者传入的外部配置，**属性**是对象的全部内部状态。`__init__` 里可以：

- 把参数直接挂到 `self` 上（1:1 映射）
- 用参数派生出更多内部属性（1:N 映射）

```python
def __init__(self, client, model, max_iterations, verbose):  # 4 个参数
    # ① 参数 → 属性（1:1）
    self.client = client
    self.model = model

    # ② 内部创建（调用者不需要知道这些）
    self.architect_tools = ToolRegistry()
    self.architect = Agent(name="架构师", ...)
    self.programmer = Agent(name="程序员", ...)
    self.tester = Agent(name="测试员", ...)
```

这类似 Java 的**构造器注入 + 工厂模式**组合，只是 Python 不需要 Spring 容器，直接写在 `__init__` 里。

---

## 3. 调用实例方法时为什么不用传 `self`？

`team.run(requirement)` 在运行时**等价于** `TeamOrchestrator.run(team, requirement)`。

Python 的 **descriptor 协议**在背后自动把实例绑到 `self` 上：

| 调用方式 | 写法 | self 谁传？ |
|------|------|------|
| 通过**实例**调用 | `team.run("任务")` | Python **自动**传 |
| 通过**类**调用 | `TeamOrchestrator.run(team, "任务")` | **手动**传 |

```python
# 鬼畜但合法：bound method 已经"锁"住了 team
method = team.run
method("任务")  # 不需要再传 self
```

**定义时写 `self`，调用时不用管它。**

---

## 4. `with` 关键字是干嘛的？

`with` = **自动善后**。凡是需要"用完记得还"的资源，`with` 保证不会忘。

```python
# 不用 with — 你得出场善后
f = open("data.txt")
f.read()
f.close()  # ⚠️ 忘了 → 资源泄漏

# 用 with — Python 帮你善后
with open("data.txt") as f:
    f.read()
# ↑ 出了缩进块，不管正常还是异常，f.close() 一定执行
```

底层机制：

```
进入 with 块 → 调用 __enter__()  获取资源
离开 with 块 → 调用 __exit__()   释放资源（异常也执行）
```

---

## 5. Python 还有哪些类似 `with` 的特殊关键字？

这些叫**复合语句**（带缩进块的）：

| 关键字 | 作用 | 典型场景 |
|------|------|------|
| `if/elif/else` | 条件分支 | 判断逻辑 |
| `for/while` + `break/continue` | 循环 | 遍历/重复 |
| `try/except/finally` | 异常处理 | 兜底错误 |
| `with` | 资源管理 | 自动善后 |
| `match/case` | 模式匹配 | 3.10+ |
| `def/class` | 定义 | 函数/类 |
| `async/await` | 异步 | 协程 |

三兄弟的关系：`try`（兜底异常）、`finally`（无论如何都执行）、`with`（自动善后）。

常用上下文管理器：

```python
with open(...)           # 文件
with lock:               # 线程锁
with TemporaryDirectory() # 临时目录（用完删除）
with ThreadPoolExecutor() # 线程池
```

---

## 6. Python 和 Java 的循环有什么区别？

**核心差异**：Python 靠遍历可迭代对象，Java 靠计数。

| 特性 | Python | Java |
|------|------|------|
| 经典 `for(;;)` | ❌ 没有 | ✅ |
| `for...in` / 增强 for | ✅ 原生 | ✅ |
| `while` | ✅ 一样 | ✅ |
| `do...while` | ❌（用 `while True + break`） | ✅ |
| `for/while...else` | ✅ | ❌ |
| 解构遍历 | ✅ `for k,v in dict` | ❌ |
| 标签跳转 | ❌ | ✅ `break label` |

Python 特有的 `for...else`：

```python
for item in items:
    if found:
        break
else:
    print("遍历完了也没找到")  # 只有没被 break 时才执行
```

Python 想计数就用 `range()`：

```python
for i in range(10):          # 0~9
for i, item in enumerate(items, 1):  # 带序号，从 1 开始
```

---

## 7. `enumerate` 和 f-string 语法解释

```python
for i, it in enumerate(result["iterations"], 1):
    print(f"🔄 迭代 {i} — {'✅ 通过' if it['passed'] else '❌ 不通过'}")
```

逐层拆解：

| 写法 | 含义 |
|------|------|
| `enumerate(seq, 1)` | 给序列编上号，从 1 开始，返回 `(序号, 元素)` 对 |
| `f"...{expr}..."` | f-string，花括号内的 Python 表达式会被求值并插入 |
| `A if cond else B` | 三元表达式，等价 Java 的 `cond ? A : B` |
| `'─' * 40` | 字符串乘法，重复 40 次 |
| `text[:800]` | 切片，取前 800 个字符 |
| `d["key"]` | 字典取值，等于 Java 的 `map.get("key")` |

---

## 8. Python 的各种括号和符号

### 括号三兄弟

| 括号 | 用途 |
|------|------|
| `()` 圆括号 | 函数调用、元组、表达式分组、生成器 |
| `[]` 方括号 | 列表、索引/切片、列表推导式 |
| `{}` 花括号 | 字典、集合、f-string 插值 |

```python
# ()
len("abc")                     # 函数调用
point = (3, 4)                 # 元组（不可变）
g = (x*2 for x in range(10))   # 生成器表达式

# []
nums = [1, 2, 3]               # 列表
first = nums[0]                # 索引
sub = nums[1:5]                # 切片
evens = [x for x in nums if x % 2 == 0]  # 推导式

# {}
d = {"name": "Alice"}          # 字典
ids = {1, 2, 3}                # 集合（去重）
print(f"你好 {name}")           # f-string 插值
```

### 其他常见符号

| 符号 | 作用 | 示例 |
|------|------|------|
| `:` | 代码块开头 / 切片 / 字典分隔 / 类型注解 | `if x:` `[1:3]` `{"k":"v"}` `x: int` |
| `->` | 返回值类型注解 | `def f() -> str:` |
| `\|` | 类型联合 (Python 3.10+) | `str \| None` |
| `@` | 装饰器 | `@staticmethod` |
| `*` | 乘法 / 序列重复 / 解包 | `"─"*40` `*args` |
| `**` | 幂 / 字典解包 | `2**10` `**kwargs` |

---

## 9. Python 常用内置模块有哪些？

### 最常用

| 模块 | 用途 | 项目中用到的 |
|------|------|------|
| `json` | JSON 序列化 | ✅ `json.dumps/loads` |
| `re` | 正则表达式 | ✅ `re.search` |
| `os` / `os.path` | 文件路径、环境变量 | ✅ `os.path.join` |
| `pathlib` | 面向对象的路径操作 | ✅ `Path(__file__).parent` |
| `datetime` | 日期时间处理 | ✅ Web 模块 |
| `typing` | 类型注解 | ✅ `Annotated` `Optional` |

### 按领域分类

| 领域 | 模块 |
|------|------|
| 数据结构 | `collections` (Counter, defaultdict), `itertools`, `functools` (lru_cache), `enum` |
| 系统 | `sys` (argv, exit), `subprocess`, `argparse`, `logging` |
| 并发 | `threading`, `multiprocessing`, `concurrent.futures`, `asyncio` |
| 网络 | `urllib`, `http`, `socket` |
| 安全 | `hashlib`, `hmac`, `base64` |
| 开发 | `unittest`, `pdb`, `traceback`, `dataclasses` |
| 数学 | `math`, `random`, `decimal`, `statistics` |

---

*持续更新中…*
