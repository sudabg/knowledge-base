---
name: feishu-bitable-creator
description: |
  创建飞书多维表格（Bitable）的专用技能。覆盖：创建App、配置字段（重命名默认+新增）、插入数据、自检验证。

  **触发条件**：用户说"创建多维表格"、"建一个表格"、"做bitable"、"帮我建个飞书表"、"数据表"。

  **核心原则**：永远利用默认字段（重命名而非新增），永远清除默认空行，永远自检。
---

# 飞书多维表格创建技能

## ⚠️ 前置检查

1. 确认用户给了：表名、字段列表（名称+类型+选项）、示例数据
2. 如果缺信息，问清楚再动手——不要猜
3. 视图工具（feishu_bitable_app_table_view）当前被禁用，视图需求需告知用户

## 🚨 铁律（血的教训）

1. **重命名默认字段，不要新增** — 创建App自带4个字段(文本/单选/日期/附件)，直接改名即可
2. **永远清除默认空行** — 创建App自带10条空记录，必须先删
3. **单选/多选options通过写入记录自动创建** — tool的property参数有bug，传options必报WrongRequestBody
4. **公式字段表达式无法通过tool设置** — 需告知用户
5. **人员字段缺open_id时留空** — 不要编造ID
6. **串行写入记录，每次间隔0.5s** — 并发写会报WriteConflict

## 📋 执行流程（6步）

### Step 1: 创建App

```json
feishu_bitable_app.create → { name: "用户给的表名" }
```

获取返回的 `app_token` 和默认 `table_id`。

### Step 2: 改名数据表

```json
feishu_bitable_app_table.patch → { app_token, table_id, name: "用户指定的表名" }
```

### Step 3: 配置字段

**先删除默认空行和多余字段，再新增字段。**

3a. 列出当前字段和记录：

```json
feishu_bitable_app_table_field.list → { app_token, table_id }
feishu_bitable_app_table_record.list → { app_token, table_id, page_size: 500 }
```

3b. 批量删除所有空记录：

```json
feishu_bitable_app_table_record.batch_delete → { app_token, table_id, record_ids: [...] }
```

3c. 重命名默认字段（对照需求）：

```json
feishu_bitable_app_table_field.update → { app_token, table_id, field_id, field_name: "新名称" }
// ⚠️ 不要传 property 参数！会报错
```

3d. 删除不需要的默认字段：

```json
feishu_bitable_app_table_field.delete → { app_token, table_id, field_id }
```

3e. 新增需求中没有默认对应的字段：

```json
feishu_bitable_app_table_field.create → { app_token, table_id, field_name, type }
// ⚠️ 不要传 property 参数！会报错
```

### Step 4: 插入数据

```json
feishu_bitable_app_table_record.batch_create → { app_token, table_id, records: [...] }
```

**值格式**（详见 [references/field-types.md](references/field-types.md)）：
- 文本：直接字符串 `"任务名称"`
- 单选：字符串 `"选项名"`（自动创建选项）
- 多选：字符串数组 `["选项1","选项2"]`
- 日期：毫秒时间戳 `1774800000000`
- 人员：`[{id: "ou_xxx"}]`（缺ID时留空）
- 数字：直接数字 `58000`
- 附件：需先上传到表格（本次不涉及）

**补齐选项**：如果需求有6个选项但测试数据只用了3个，需插入占位记录补齐剩余选项。

### Step 5: 自检（必须执行）

```json
// 重新获取字段列表
feishu_bitable_app_table_field.list → { app_token, table_id }
// 重新获取记录列表
feishu_bitable_app_table_record.list → { app_token, table_id }
```

**自检清单**：
- [ ] 数据表名称正确
- [ ] 字段数量 = 需求数量（无多余、无遗漏）
- [ ] 每个字段名称和类型正确
- [ ] 单选/多选选项齐全（含未在测试数据中出现的选项）
- [ ] 记录数 = 测试数据数（无空行）
- [ ] 每条记录字段值正确
- [ ] 日期值显示正确

### Step 6: 报告结果

格式化输出：
- 表名 + 链接
- 字段清单（名称、类型、选项）
- 记录清单
- 未完成项及原因（如视图禁用、人员缺ID）

## 🚫 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| WrongRequestBody (property) | tool的property参数bug | 不传property，options通过写入记录自动创建 |
| 10条空行混入数据 | 没清除默认空记录 | Step 3b先清空 |
| 字段重复（8个而非6个） | 新增字段而非重命名默认字段 | Step 3c重命名，不是create |
| 选项不全 | 测试数据没覆盖所有选项 | 用占位记录补齐 |
| 人员字段为空 | 缺open_id | 留空，报告用户 |
