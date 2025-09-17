# 用户实验介绍：热身任务

## 实验环境配置

请通过以下命令配置环境，用于测试编辑结果：

```bash
conda create --name env_1 python=3.9 -y
conda activate env_1
```

## 任务介绍

Sentry 是一个开源的应用监控和错误追踪平台，帮助开发者实时发现、分析和修复生产环境中的问题。

Sentry 在 `src/sentry/rules/processor.py` 中定义了类 `RuleProcessor`，该类的实例负责从事件处理管道中接收事件，根据配置的规则进行处理和过滤。

在开发的早期，Sentry 的开发者为 `RuleProcessor` 定义了初始化参数 `is_sample`, 是一个布尔值，在告警规则处理阶段，根据 `is_sample` 来判断事件是否为采样数据。随着开发的进展，Sentry 团队决定从 `RuleProcessor` 中移除 `is_sample` 参数。如下图所示：
![init_edit](./images/init_edit.png)

你可以前往 [`src/sentry/rules/processor.py`](src/sentry/rules/processor.py)，复制以下内容完成该初始修改：

```python
    def __init__(self, event, is_new, is_regression):
```

请你在完成该初始修改后，找到所有受到该编辑影响的位置，并完成后续修改。

> ⚠️ **温馨提示**
>
> * **初始编辑包含在内**，一共需要完成 **7** 处修改
>
> * 所有的修改都不需要新增/删除/重命名任何文件
>
> * 你可以在项目根目录下运行 `python count.py` 来查看和统计已经完成的编辑数量
>
> * 编辑数量**仅供参考**，请根据[验证修改](#验证修改)来判断是否完成修改目标

## 编辑描述

当你需要输入编辑描述时，你可以直接复制以下内容：

```bash
ref(rules): Remove is_sample as an argument to RuleProcessor
```

如果你所在的实验组使用的后端模型是 Claude Code，你可以输入任意内容和 Claude Code 沟通。

## 验证修改

请运行一下命令验证修改是否成功

```bash
python -m test.run
```

当修改正确时，你应该看到以下内容：

```bash
Test 1 passed.
Test 2 passed.
Test 3 passed.
Test 4 passed.
```

恭喜你成功完成该任务，你可以告知实验负责人，停止录屏，整理需要提交的内容，并在**所有任务**完成后，打包提交。
