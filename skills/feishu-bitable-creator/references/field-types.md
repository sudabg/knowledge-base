# 字段类型速查

## 默认字段（创建App自带）

| 默认字段 | type | 处理方式 |
|---------|------|---------|
| 文本 | 1 (Text) | 重命名为需求名称 |
| 单选 | 3 (SingleSelect) | 重命名（options通过记录写入自动创建） |
| 日期 | 5 (DateTime) | 重命名（如需要）或删除 |
| 附件 | 17 (Attachment) | 通常删除 |

## type编号对照

| type | ui_type | 含义 | record写入格式 |
|------|---------|------|---------------|
| 1 | Text | 文本 | 直接字符串 |
| 2 | Number | 数字 | 直接数字 |
| 3 | SingleSelect | 单选 | 字符串（如`"未开始"`） |
| 4 | MultiSelect | 多选 | 字符串数组（如`["小红书","抖音"]`） |
| 5 | DateTime | 日期 | 毫秒时间戳（如`1774800000000`） |
| 7 | CheckBox | 复选框 | boolean |
| 11 | User | 人员 | `[{id: "ou_xxx"}]` |
| 15 | Url | 超链接 | `{link: "URL", text: "显示文本"}` |
| 17 | Attachment | 附件 | 需先上传到表格 |
| 20 | Formula | 公式 | 只读，不可tool设置表达式 |
| 1001 | CreatedTime | 创建时间 | 自动 |
| 1002 | ModifiedTime | 修改时间 | 自动 |

## 日期转时间戳

```python
import datetime
dt = datetime.datetime(2026, 3, 30, 0, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
ts = int(dt.timestamp() * 1000)  # 毫秒
```

## 空行处理

创建App后默认有10条空记录。必须先 `record.list` 获取所有record_id，然后 `record.batch_delete` 清除。

## 选项自动创建

写入record时，如果字段值是新的选项名，飞书会自动在该字段创建该选项。
无需预先通过field.update设置options（tool的property参数有bug会报错）。
