# JSON 数据对比 Skill

## 一、概述

对比两个 JSON 接口返回数据的差异，支持不同命名风格（驼峰/下划线）字段映射、JsonPath 数据提取（含点击可视化树选取路径）、自定义联合主键匹配，输出结构化对比结果并支持 CSV 导出。

**适用场景**：
- 新旧接口返回数据一致性验证
- 接口重构后数据回归对比
- 不同环境（测试/生产）数据差异排查
- 单条记录字段级对比（非数组对象直接对比）

## 二、输入参数

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| new_json | 是 | 新接口JSON数据 | `{"code":"000000","data":{"list":[...]}}` |
| old_json | 是 | 旧接口JSON数据 | `{"code":200,"data":{"dataList":[...]}}` |
| new_path | 否 | 新数据JsonPath | `$.data.list` |
| old_path | 否 | 旧数据JsonPath | `$.data.dataList` |
| primary_keys | 否 | 自定义联合主键（逗号/加号/空格分隔） | `skuId, storeId` 或 `id` |
| ignore_fields | 否 | 忽略对比字段（逗号/加号/空格分隔，自动适配 camel/snake 与内置映射） | `updateTime, dealPrice` |

## 三、核心能力

### 3.1 JsonPath 数据提取

支持路径格式：
- `$.data.list` - 对象属性访问
- `$.data.list[0]` - 数组下标
- `$.data.list[0].items` - 混合路径

**路径选取功能**：前端支持点击可视化树节点自动填充 JsonPath，无需手动输入。

**非数组兼容**：当 JsonPath 提取结果为单个对象（dict）时，自动包装为单元素数组进行对比，支持单条记录字段级直接对比。

### 3.2 字段映射（驼峰 ↔ 下划线）

三级匹配策略（优先级从高到低）：
1. 内置 `FIELD_MAP` 映射表精确匹配
2. 字段名直接相等
3. 自动 camelCase ↔ snake_case 互转

```
shopName    ↔ shop_name
skuId       ↔ sku_id
dealPrice   ↔ deal_price
storeId     ↔ store_id
...
```

### 3.3 自定义联合主键

支持用户自定义主键字段（输入框可编辑），用于数组记录的匹配关联：
- 多字段分隔：逗号 `,`、加号 `+`、空格均可
- 自动 camel↔snake 互转（输入 `skuId` 也能匹配到数据中的 `sku_id`）
- 留空或匹配失败时回退默认 `skuId + storeId`
- 单对象无主键时使用 `__single__` 统一匹配

功能：
- 识别仅存在于某一方的记录（含完整记录详情）
- 逐字段对比共有记录的值差异
- 补充旧侧多余字段为差异项

### 3.4 智能类型转换

对比时自动处理类型差异：
- `storeId: "1005517860"` vs `store_id: 1005517860` → 一致
- `null` vs `null` → 一致
- 数值精度对比（float 等值判定）
- 字符串自动 trim 后对比

### 3.5 输出内容

每条记录输出：
- new_data 字段名 + 值（完整显示，无截断） + 数据类型
- old_data 字段名 + 值（完整显示，无截断） + 数据类型
- 对比结果（一致 ✓ / 差异 ✕）

### 3.6 结果过滤与搜索

**全局级**：全部 / 差异 / 一致 / 单边 四个 Tab 过滤 + 主键关键词搜索
**组内级**：每条记录卡片内独立的 全部 / 差异 / 一致 字段过滤

### 3.7 结果导出

支持导出 CSV（UTF-8 BOM，Excel 可直接打开），包含：主键、新字段、新值、新类型、旧字段、旧值、旧类型、是否一致。

### 3.8 忽略指定字段

支持用户配置不参与字段级对比的字段：
- 多字段分隔：逗号 `,`、加号 `+`、空格均可
- 自动 camel↔snake 互转（输入 `dealPrice` 可忽略 `deal_price`）
- 自动兼容内置 `FIELD_MAP`（输入新侧或旧侧字段名均可）
- 被忽略字段不计入差异、不在结果表格与 CSV 中展示

## 四、技术架构（前后端分离）

```
demo/
├── server/                # 后端 (Flask + CORS)
│   └── app.py            # API 服务 :5000
│       ├── POST /api/format    # JSON格式化
│       ├── POST /api/validate  # JSON校验
│       ├── POST /api/compare   # 数据对比（支持自定义主键）
│       └── POST /api/export    # 导出CSV
└── frontend/              # 前端 (Vue3 + Vite)
    └── src/
        ├── api/index.js          # API封装(axios) + CSV下载
        ├── utils/
        │   ├── toast.js          # 全局Toast提示
        │   └── demoData.js       # 示例数据（一键加载）
        ├── style.css             # 全局Design Tokens + 组件样式
        ├── App.vue               # 主页面（导航+配置区+双面板+结果区）
        └── components/
            ├── JsonPanel.vue     # JSON输入面板（源码/可视化Tab+工具栏+选取模式）
            ├── JsonTree.vue      # JSON可视化树（支持选取路径交互）
            ├── JsonNode.vue      # 递归树节点（语法高亮+折叠+路径选取）
            └── CompareResult.vue # 对比结果（统计+过滤+搜索+表格+导出）
```

## 五、启动方式

### 后端
```bash
pip install flask flask-cors
python demo/server/app.py
# 服务运行在 http://localhost:5000
```

### 前端
```bash
cd demo/frontend
npm install
npm run dev
# 服务运行在 http://localhost:5173
```

## 六、API 接口说明

### POST /api/format
格式化JSON文本。
- 请求: `{"text": "原始JSON字符串"}`
- 响应: `{"ok": true, "formatted": "格式化后JSON"}` 或 `{"ok": false, "error": "第N行第M列 - 错误描述"}`

### POST /api/validate
校验JSON格式。
- 请求: `{"text": "JSON字符串"}`
- 响应: `{"ok": true, "message": "JSON格式正确"}` 或 `{"ok": false, "error": "第N行第M列 - 错误描述"}`

### POST /api/compare
对比两组JSON数据。
- 请求:
```json
{
  "new_json": "新数据JSON字符串",
  "old_json": "旧数据JSON字符串",
  "new_path": "$.data.list",
  "old_path": "$.data.dataList",
  "primary_keys": "skuId, storeId",
  "ignore_fields": "updateTime, dealPrice"
}
```
- `primary_keys`：可选，字符串（逗号/加号/空格分隔）或数组。留空使用默认 skuId+storeId。
- `ignore_fields`：可选，字符串（逗号/加号/空格分隔）或数组。自动兼容 camel/snake 命名与内置字段映射。
- 响应:
```json
{
  "ok": true,
  "result": {
    "totalNew": 20,
    "totalOld": 20,
    "onlyInNew": [{"key": "xxx_yyy", "record": {...}}],
    "onlyInOld": [{"key": "xxx_yyy", "record": {...}}],
    "commonCount": 18,
    "diffCount": 3,
    "comparisons": [
      {
        "key": "67287295489_1005517860",
        "hasDiff": false,
        "fields": [
          {"newField": "skuId", "newVal": 67287295489, "newType": "int", "oldField": "sku_id", "oldVal": 67287295489, "oldType": "int", "same": true}
        ]
      }
    ]
  }
}
```

### POST /api/export
导出对比结果为 CSV。
- 请求: `{"result": <上述compare响应中的result对象>}`
- 响应: `text/csv` 文件流（UTF-8 BOM）

## 七、前端功能

### 7.1 顶部导航
- 品牌标识 + 加载示例按钮 + 清空按钮

### 7.2 配置区
- **新数据 JsonPath** 输入框 + 🎯选取按钮（从可视化树点选路径）
- **旧数据 JsonPath** 输入框 + 🎯选取按钮
- **联合主键** 可编辑输入框（默认 `skuId, storeId`，支持逗号/加号/空格分隔）
- **忽略字段** 可编辑输入框（支持逗号/加号/空格分隔，自动适配 camel/snake 命名）
- **开始对比** 按钮

### 7.3 JSON 输入面板（双面板）
- **源码/可视化** 双 Tab 切换
- **可视化树**：语法高亮、类型标注（badge）、折叠/展开、虚线缩进、数组索引前缀
- **工具栏**：格式化、校验、压缩、复制、清空 + 字符计数
- **状态提示**：未校验 / JSON格式正确（绿） / 错误信息（红）
- **选取模式**：点击树节点自动填充 JsonPath，橙色高亮选中节点，自动退出

### 7.4 对比结果区
- **统计卡片**：新数据总数、旧数据总数、共有记录、差异记录、仅新存在、仅旧存在
- **全局过滤**：全部 / 差异 / 一致 / 单边 + 主键搜索
- **记录卡片**（默认折叠）：
  - 主键 + 差异/一致标签 + 字段计数
  - **组内过滤**：全部 / 差异 / 一致（独立状态，互不干扰）
  - 字段对比表格：新字段、新值（完整无截断、自动换行）、类型、旧字段、旧值、类型、结果
  - 差异行红色高亮
- **单边记录卡**：仅新/仅旧标签 + 可展开查看完整记录 JSON
- **导出 CSV** 按钮

### 7.5 Toast 提示
- 操作反馈（成功/错误/提示）全局右上角弹出

## 八、字段映射配置

当前内置 LBS 价格星级业务字段映射，可在 `server/app.py` 的 `FIELD_MAP` 中扩展：

```python
FIELD_MAP = {
    "skuId": "sku_id",
    "shopName": "shop_name",
    "dealPrice": "deal_price",
    "storeId": "store_id",
    "status": "status",
    "tags": "tags",
    # ... 40+ 业务字段已内置
    # 新增映射在此添加
}
```

即使未在映射表中，后端也会自动尝试 camelCase ↔ snake_case 互转匹配。

## 九、已实现能力总结

| 能力 | 状态 |
|------|------|
| JsonPath 数据提取 | ✅ |
| 点击可视化树选取路径 | ✅ |
| 自定义联合主键 | ✅ |
| 非数组（单对象）对比 | ✅ |
| 驼峰/下划线字段自动映射 | ✅ |
| 智能类型转换对比 | ✅ |
| 值完整显示（无截断） | ✅ |
| 全局过滤（全部/差异/一致/单边） | ✅ |
| 组内字段过滤（全部/差异/一致） | ✅ |
| 主键搜索 | ✅ |
| 结果默认折叠 | ✅ |
| CSV 导出 | ✅ |
| 忽略指定字段 | ✅ |
| 示例数据一键加载 | ✅ |
| Toast 操作反馈 | ✅ |

## 十、扩展方向

- 支持用户自定义字段映射（前端配置界面）
- 支持批量文件对比
- 对比结果导出 Excel（xlsx）
- 对比历史记录保存
