# Exam Question Bank for Chinese Driving Test Subject 1 & Subject 4
科目一、四考试题库

### 快速使用：刷题
- 在release中下载并运行bank_practice.exe（或者手动下载全库，运行[bank_practice.py](bank_practice.py)脚本）
- 支持科一、科四选择，支持刷题、背题、模拟考试，支持刷全部题、只刷没做过的题、只刷错题、刷指定题。支持刷题记录，支持题目图片查看。

### 题库说明：
- [Question-Bank.json](Question-Bank.json)为经过新规（截止2026.7.28）纠正的题库，基于[2022年第三方题库](https://github.com/doupoa/DrivingTestSubjectOne)（[documents/Question-Bank-2022.json](documents/Question-Bank-2022.json)），原题库包含2022年的新规但不包含2025年的新规，也不包含2025新规题，修正版题库根据新规对题库中过时的题目做了修正（新规：2025.1.1 第172号）
- 官方不公开驾考科目一 / 科目四题库，所有第三方软件题库均通过考生回忆汇总和其他方式取得，但与官方题相似
- 第三方软件题库与本题库基本相似，但会多一些专为新规设计的新规题。
- 根据实际考试经历（~~*你怎么知道我考了99分*~~），本题库和第三方软件题库与考试正式题库的原题率均不算特别高，但题目相似率很高。
- 题库共约 4378 题，包含科一、科四
- 题库中图片通过 url 在线连接第三方呈现

### 资料说明：
- [documents/JKBD.pdf](documents/JKBD.pdf) 是驾考宝典科目一课程 PPT 截取图合集
- [documents/study_manual.md](documents/study_manual.md) 是 AI 根据科目一题库和新规整理的知识点学习手册
- [documents/change172.txt](documents/change172.txt) 是 2025.1.1 的令第172号新规

### 题库json格式说明
| 字段名 | 含义 |
|---|---|
| `id` | 题目唯一 ID |
| `question` | 题干 |
| `answer` | 正确答案 |
| `answerSkill` | 答题技巧 |
| `answerSkillExplain` | 答案解析 |
| `remark` | 备注（HTML 格式，常为法规出处） |
| `itemsTitleArray` | 选项标题 |
| `itemsDescArray` | 选项描述 |
| `url` | 题目主图（CDN，.jpg） |
| `coverUrl` | 封面/讲解配图（CDN，.png） |
| `aliyVid` | 阿里云视频讲解 ID |
| `vedioExplainFlag` | 是否有视频讲解 |
| `chapterId` | 章节 ID |
| `subject` | 科目 |
| `type` | 题型 |
| `typeDesc` | 题型描述 |
| `regionCode` | 地区码 |
| `style` | 样式 |
| `newRuleFlag` | 新规标记 |
| `secretFlag` | 密题标记 |
| `difficulty` | 难度等级 |
| `errorRate` | 错误率（%） |
| `easyErrorFlag` | 易错标记 |
| `errorProneFlag` | 易错标记 |
| `score` | 分值 |
| `flag` | 标记 |
| `selectedFlag` | 选中标记 |
| `versionNo` | 版本号 |

### 其他
- 题库来源：[https://github.com/doupoa/DrivingTestSubjectOne](https://github.com/doupoa/DrivingTestSubjectOne)
- 刷题时，已做题目情况记录在bank_log.json，已做题目下载的图片在.bank_img_cache文件夹中。
