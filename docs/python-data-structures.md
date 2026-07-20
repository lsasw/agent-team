# Python 数据结构与案例

## 一、内置基础类型

### 1. list — 列表（可变序列）

有序、可修改、允许重复。

```python
# ── 创建 ──
nums = [1, 2, 3]
mixed = [1, "hello", 3.14, None]
nested = [[1, 2], [3, 4]]
copied = list(nums)

# ── 增删改查 ──
nums.append(4)           # 末尾追加  → [1, 2, 3, 4]
nums.insert(1, 99)       # 指定位置插 → [1, 99, 2, 3, 4]
nums.extend([5, 6])      # 合并另一个  → [..., 5, 6]
nums.pop()               # 弹出末尾(返回) → 6
nums.pop(1)              # 弹出索引 1
nums.remove(3)           # 按值删除第一个匹配
nums[0] = 100            # 按索引修改

# ── 切片（不复制原列表，创建新列表）──
nums = [0, 1, 2, 3, 4, 5]
nums[1:4]    # [1, 2, 3]    索引 1 到 3
nums[:3]     # [0, 1, 2]    从头到索引 2
nums[2:]     # [2, 3, 4, 5] 从索引 2 到尾
nums[::2]    # [0, 2, 4]    步长 2
nums[::-1]   # [5, 4, 3, 2, 1, 0]  反转

# ── 列表推导式（Python 的灵魂操作）──
squares = [x**2 for x in range(10)]              # [0, 1, 4, 9, ..., 81]
evens = [x for x in range(20) if x % 2 == 0]     # 带过滤
pairs = [(x, y) for x in "ab" for y in "12"]     # 笛卡尔积

# ── 实用方法 ──
nums.sort()               # 原地排序
nums.sort(reverse=True)   # 降序
sorted_nums = sorted(nums) # 不改变原列表
len(nums)                  # 长度
3 in nums                  # 是否包含 → True/False
nums.index(3)              # 首次出现的索引
nums.count(3)              # 出现次数
",".join(["a", "b", "c"])  # "a,b,c"（字符串列表才能 join）
```

**项目中的真实用法** (`agent.py`)：

```python
# 消息历史 — 用列表管理对话上下文
messages = [
    {"role": "system", "content": self._build_system_message()},
    {"role": "user", "content": user_msg},
]
messages.append({"role": "assistant", "content": text})
messages.append({"role": "user", "content": f"Observation: {result}"})
```

---

### 2. tuple — 元组（不可变序列）

有序、不可修改、可以当字典的 key。

```python
# ── 创建（逗号才是元组的本体，括号只是可选的）──
t = (1, 2, 3)
t = 1, 2, 3           # 等价！括号不是必须的
single = (1,)          # 单元素必须加逗号，否则 (1) 只是数字 1
empty = ()
t = tuple([1, 2, 3])   # 从可迭代对象构造

# ── 解包（unpacking）──
point = (3, 4)
x, y = point           # x=3, y=4

a, b, *rest = (1, 2, 3, 4, 5)  # a=1, b=2, rest=[3, 4, 5]

# ── 典型场景 ──
# ① 函数返回多个值（底层就是返回一个元组）
def get_user():
    return 1, "alice", "alice@test.com"
id, name, email = get_user()

# ② 不可变性 — 适合做常量、字典 key
COLORS = ("red", "green", "blue")
mapping = {("user", 1): "alice"}   # 元组可哈希，可做 key
```

**项目中** (`enumerate` 返回的就是 (索引, 元素) 元组)：

```python
for i, it in enumerate(result["iterations"], 1):
    #    ↑ 这里就在做元组解包
    print(f"迭代 {i} — {it['code'][:800]}")
```

---

### 3. dict — 字典（键值对映射）

无序（3.7+ 保证插入顺序）、key 必须可哈希。

```python
# ── 创建 ──
d = {"name": "Alice", "age": 30}
d = dict(name="Alice", age=30)         # 另一种构造方式
d = dict([("name", "Alice"), ("age", 30)])

# ── 增删改查 ──
d["email"] = "a@test.com"    # 新增/修改
d.get("email", "unknown")    # 安全取值，不存在返回默认值
d.setdefault("role", "user") # 如果不存在则设置，并返回当前值
d.pop("age")                 # 删除并返回值
del d["name"]                # 删除（不返回值）
d.update({"city": "NY"})     # 合并/覆盖

# ── 遍历 ──
for k, v in d.items():       # 键值对（最常用）
    print(f"{k}: {v}")

for k in d:                  # 只键
    print(k)

for v in d.values():         # 只值
    print(v)

# ── 字典推导式 ──
squares = {x: x**2 for x in range(5)}    # {0:0, 1:1, 2:4, 3:9, 4:16}
flipped = {v: k for k, v in d.items()}   # 键值反转

# ── 合并（Python 3.9+）：| 运算符 ──
a = {"x": 1, "y": 2}
b = {"y": 99, "z": 3}
merged = a | b    # {"x": 1, "y": 99, "z": 3}（重复键取后面的）
```

**项目中的真实用法** (`tools.py` — 工具注册表、`team.py` — 返回结果)：

```python
# 工具注册表：名字 → 工具对象
self._tools: dict[str, Tool] = {}

# 团队运行结果
result = {
    "requirement": requirement,
    "design": "",
    "iterations": [],
    "final_code": "",
    "passed": False,
}

# JSON 输出（字典序列化）
params = {"path": "fib.py", "content": code}
json.dumps(params, ensure_ascii=False)
```

---

### 4. set — 集合（无序、不重复）

基于哈希表，查找速度 O(1)。

```python
# ── 创建 ──
s = {1, 2, 3}
s = set([1, 2, 2, 3])   # {1, 2, 3}  自动去重
empty = set()            # 空集合只能用 set()，{} 是空字典

# ── 集合运算（最经典用途）──
a = {1, 2, 3}
b = {2, 3, 4}

a | b       # 并集 {1, 2, 3, 4}
a & b       # 交集 {2, 3}
a - b       # 差集 {1}        a 有 b 没有的
a ^ b       # 对称差 {1, 4}   只在一边的

# ── 增删查 ──
s.add(4)               # 添加
s.remove(4)            # 删除，不存在报错
s.discard(4)           # 安全删除，不存在不报错
3 in s                 # 是否存在 → True/False（很快！）

# ── 经典场景 ──
# ① 去重
unique = list(set([1, 1, 2, 2, 3]))  # [1, 2, 3]

# ② 去重保留顺序（Python 3.7+）
unique = list(dict.fromkeys([3, 1, 1, 2, 3]))  # [3, 1, 2]
```

**项目中的真实用法** (`team.py` — 停滞检测)：

```python
def extract_issues(text: str) -> set:
    lines = re.findall(r"^[\s]*[-*]\s*(.+)", text, re.MULTILINE)
    return set(line.strip().lower() for line in lines)
    #          ↑ 用集合去重 + 快速交集运算

prev = extract_issues(prev_review)
curr = extract_issues(curr_review)
overlap = len(prev & curr) / len(prev | curr)  # Jaccard 相似度
```

---

### 5. frozenset — 不可变集合

集合的"冻结"版，可以当字典 key。

```python
fs = frozenset([1, 2, 3])
# fs.add(4)  # AttributeError! 不可变

# 主要用途：做字典的 key
d = {frozenset(["read", "write"]): "读写权限"}  # ✅
d = {set(["read", "write"]): "读写权限"}          # ❌ TypeError
```

---

## 二、collections 模块（进阶数据结构）

```python
from collections import namedtuple, deque, Counter, defaultdict, OrderedDict, ChainMap
```

### 1. namedtuple — 有名字的元组

轻量级"类"，比普通类少样板代码，比元组可读性高。

```python
# ── 定义 ──
Point = namedtuple("Point", ["x", "y"])
User = namedtuple("User", "id name email")

# ── 使用 ──
p = Point(3, 4)
p.x       # 3     ← 比 p[0] 可读得多
p.y       # 4

alice = User(1, "alice", "a@test.com")
alice.name   # "alice"

# 本质还是元组
x, y = p     # 仍然可以解包
```

**对比 3 种方式**：

```python
# 元组 — 难读
user = (1, "alice", "a@test.com")
user[1]  # 这是啥？还得回去看定义

# namedtuple — 可读 + 不可变 + 轻量
User = namedtuple("User", "id name email")
user = User(1, "alice", "a@test.com")
user.name  # ✅ 清晰

# dataclass — 可读 + 可变（5行代码）
from dataclasses import dataclass
@dataclass
class User:
    id: int
    name: str
    email: str
```

---

### 2. deque — 双端队列

两端插入 O(1)，比 list 的 insert(0)/pop(0) 快得多（list 是 O(n)）。

```python
from collections import deque

dq = deque([1, 2, 3])
dq.append(4)       # 右边加 → [1, 2, 3, 4]
dq.appendleft(0)   # 左边加 → [0, 1, 2, 3, 4]
dq.pop()           # 右边弹 → 4
dq.popleft()       # 左边弹 → 0

# ── 经典场景：最近 N 条历史记录 ──
history = deque(maxlen=5)   # 自动丢掉旧的
for msg in stream:
    history.append(msg)
# history 永远只保留最近 5 条
```

---

### 3. Counter — 计数器

```python
from collections import Counter

# ── 自动统计 ──
words = ["a", "b", "a", "c", "a", "b"]
c = Counter(words)
# Counter({'a': 3, 'b': 2, 'c': 1})

c.most_common(2)    # [('a', 3), ('b', 2)]  前 2 名
c["a"]              # 3
c["z"]              # 0  ← 不存在的 key 返回 0，不报错

# ── 项目场景：统计日志中的关键词频率 ──
logs = ["ERROR: timeout", "WARN: retry", "ERROR: timeout"]
error_counts = Counter(log.replace("ERROR: ", "") for log in logs if "ERROR" in log)
```

---

### 4. defaultdict — 带默认值的字典

访问不存在的 key 自动创建默认值，省去 `if key not in d`。

```python
from collections import defaultdict

# ── 对比 ──
# 普通字典
d = {}
for word in ["a", "b", "a"]:
    if word not in d:
        d[word] = 0      # 烦！
    d[word] += 1

# defaultdict
d = defaultdict(int)     # int() → 0
for word in ["a", "b", "a"]:
    d[word] += 1         # 清爽！首次访问自动初始化为 0

# ── 常用默认值 ──
d = defaultdict(int)     # 默认 0，适合计数
d = defaultdict(list)    # 默认 []，适合分组
d = defaultdict(set)     # 默认 set()，适合去重分组
d = defaultdict(str)     # 默认 ""

# ── 分组场景 ──
users_by_role = defaultdict(list)
for user in all_users:
    users_by_role[user.role].append(user)
# 不需要判断 key 是否存在！
```

---

### 5. OrderedDict — 有序字典

保持插入顺序（Python 3.7+ 普通 dict 也保序了，但 OrderedDict 多了几个方法）。

```python
from collections import OrderedDict

od = OrderedDict()
od["a"] = 1
od["b"] = 2
od.move_to_end("a")      # 把 "a" 移到最后
od.popitem(last=False)   # LIFO 或 FIFO 弹出
```

---

## 三、其他实用结构

### 1. heapq — 堆（优先队列）

最小堆：始终能以 O(log n) 取最小值。

```python
import heapq

h = [5, 1, 3, 2, 4]
heapq.heapify(h)        # 原地建堆 → [1, 2, 3, 5, 4]

heapq.heappush(h, 0)    # 插入
smallest = heapq.heappop(h)  # 弹出最小值

# 取 Top-K
largest_3 = heapq.nlargest(3, [1, 5, 2, 8, 3])   # [8, 5, 3]
```

---

### 2. array — 紧凑数组

所有元素同类型，内存比 list 小得多（类似 C 数组）。

```python
from array import array

nums = array("i", [1, 2, 3])   # 'i' = signed int
nums.append(4)
# 内存比 list 节省约 3-4 倍
```

---

### 3. dataclass — 数据类

Python 3.7+，自动生成 `__init__` `__repr__` `__eq__`。

```python
from dataclasses import dataclass, field

@dataclass
class User:
    id: int
    username: str
    email: str
    is_active: bool = True              # 有默认值的放后面
    tags: list[str] = field(default_factory=list)  # 可变默认值必须用 field

# 自动生成的 __init__
alice = User(id=1, username="alice", email="a@test.com")

# 自动生成的 __repr__
print(alice)  # User(id=1, username='alice', email='a@test.com', is_active=True, tags=[])

# 自动生成的 __eq__
alice == User(id=1, username="alice", email="a@test.com")  # True
```

---

### 4. enum — 枚举

```python
from enum import Enum

class Status(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

status = Status.RUNNING
status.value         # "running"
status == Status.RUNNING  # True
```

**项目中的适用场景**：Agent 的解析结果类型

```python
class ParseResult(Enum):
    FINAL = "final"
    ACTION = "action"
    TEXT = "text"

parsed = self._parse_response(text)
if parsed["type"] == ParseResult.FINAL.value:  # 不用硬编码字符串
    return parsed["answer"]
```

---

## 四、复杂度速查表

| 数据结构 | 索引 | 查找 | 插入 | 删除 | 适用场景 |
|------|------|------|------|------|------|
| `list` | O(1) | O(n) | 末尾 O(1), 头部 O(n) | 末尾 O(1), 头部 O(n) | 有序序列，需要索引 |
| `tuple` | O(1) | O(n) | — | — | 不可变数据，字典 key |
| `dict` | O(1) | O(1) | O(1) | O(1) | 键值映射，快速查找 |
| `set` | — | O(1) | O(1) | O(1) | 去重，成员判断，集合运算 |
| `deque` | O(1)* | O(n) | 两端 O(1) | 两端 O(1) | 队列/栈，滑动窗口 |
| `heapq` | — | — | O(log n) | O(log n)* | Top-K，优先队列 |

---

## 五、选择决策树

```
需要存什么？
  │
  │── 有键值关系 → dict (或 defaultdict 如果需要默认值)
  │
  │── 只有值，有顺序
  │   │── 要修改的 → list
  │   │── 不可变的 → tuple
  │   │── 需要两端快速插入删除 → deque
  │   │── 需要 Top-K 或优先队列 → heapq
  │   │── 需要"有名字的字段" → namedtuple 或 dataclass
  │
  │── 只要"有没有"，不关心顺序
      │── 标准的 → set
      │── 不可变的 → frozenset
      │── 需要计数的 → Counter
```
