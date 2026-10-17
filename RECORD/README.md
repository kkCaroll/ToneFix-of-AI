# 结果目录约定

本目录只放实验产生的证据，不放代码，不放文档。命名与阶段计划对应。

```
RECORD/
  probe_bash/                阶段零 无头调用执行命令的核验，六份原始流
  probe_bash.json            同上，脚本汇总
  probe_edit_path/           阶段零 改代码路径核验，八份原始流
  probe_edit_path.json       同上，脚本汇总
  phase1/                    阶段一 手工走查
    episodes.json            三次 episode 的机器可读汇总
    <任务>_<臂>_r<重复>/     每次 episode 一个目录，四件证据
      round1.jsonl             原始流，逐行事件
      改动.patch               相对起点提交的差异
      改动行数.txt             逐文件的新增与删除行数
      判分_可见.txt            脚手架重跑可见测试的尾部输出
  probe_difficulty/          阶段一补充 难度探测第一轮，自变量为代码规模
    summary.json             三次 episode 的机器可读汇总
    <任务>_<臂>_r<重复>/     三件证据，同阶段一
  probe_defect_count/        阶段一补充 难度探测第二轮，自变量为缺陷数量
    summary.json             八次 episode 的机器可读汇总
    <任务>_<臂>_r<重复>/     五件证据
      round1.jsonl             原始流，逐行事件
      改动.patch               相对起点提交的差异
      判分.json                该次 episode 的全部判分量
      判分_可见.txt            重跑可见测试的完整输出
      判分_隐藏.txt            重跑隐藏测试的完整输出
  probe_source1/             阶段二入口 来源一小样本校准
    summary.json             八个 episode 的机器可读汇总
    <任务>_<臂>_r<重复>/     五件证据，同难度探测第二轮
      round1.jsonl             首轮原始流
      round2.jsonl             第二轮原始流，仅第二轮 episode 有
      改动.patch               相对该轮起点提交的差异
      判分.json                该轮全部判分量，含并集判据与 overfit 标记
      判分_可见.txt            该轮重跑可见测试的完整输出
      判分_隐藏.txt            该轮重跑隐藏测试的完整输出
```

`probe_defect_count` 起每次 episode 多出两件证据。判分改存完整输出而非尾部，隐藏测试单独留一份，便于事后核对 `overfit_rate` 是否真为零。

## 规矩

1. 一次 episode 一个目录，目录名由任务、臂、重复次数拼成，不含空格。
2. 原始流按原样保存，不截断也不改写。任何派生量都由原始流重算得出，重算脚本与实时脚本共用同一套判定，不允许只存派生量。
3. 工作区本体留在项目树之外的一次性目录，用完即弃，不进仓库。留在仓库的是差异与判分，不是文件树。
4. 后续阶段的目录在对应阶段开始时建立，命名沿用本约定。表与图分别落在 `tables/` 与 `figures/`。
