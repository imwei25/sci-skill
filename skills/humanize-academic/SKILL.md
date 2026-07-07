---
name: humanize-academic
description: 去 AI 味 / 学术润色。把一段读起来"很 AI"的科研或医学文字改得自然、专业、像真人写的，同时保持原意、术语、数据和引用不变。针对学术写作常见的 AI 腔（套话开头、排比堆砌、空泛形容、千篇一律句长、滥用 however/moreover）。当用户说"去掉 AI 味""润色""改得像人写的""降 AI 率""让文字更自然""academic polish"时使用。
---

# 去 AI 味学术写作技能

对给定文本做两遍改写，去掉机器腔、保留学术严谨。参考 matsuikentaro1/humanizer_academic 与 blader/humanizer，聚焦科研/医学稿件。

## 常见 AI 腔（先检出，再改）
1. **套话开头/结尾**："In today's rapidly evolving...""It is worth noting that""In conclusion, ..."
2. **空泛形容**："various aspects""significant potential""a wide range of""plays a crucial role"——换成具体内容。
3. **过渡词滥用**：每段都 However/Moreover/Furthermore/Additionally——删掉大半，靠逻辑衔接。
4. **排比与三连**："efficient, effective, and reliable"式凑数并列——留最相关的。
5. **句长单调**：全是中等长句——长短交错。
6. **过度对冲/绝对**：一堆 may/might 或一堆 clearly/undoubtedly——按证据强度校准。
7. **名词化冗余**："the utilization of" → "using"；"in order to" → "to"。
8. **空转元评论**："This section will discuss..."——直接讲内容。

## 两遍改写
- **第一遍**：逐句按上面清单改：删套话、换具体、调句长、砍多余过渡词。
- **第二遍**：自问"这还有哪里一看就是 AI 写的？"再改一轮，直到读起来像领域内研究者亲笔。

## 硬约束（学术场景必须守）
- **不改科学事实、数据、数字、术语、方法**。
- **不动引用**：[n]、(Author, Year)、DOI 原样保留。
- **不夸大结论**、不加原文没有的断言。
- 保持目标语域（正式学术英文/中文），不要口语化过头。

## 用法
1. 让用户给原文（或指向 `uploads/` 里的文件）。
2. 改完给出：**改写稿** + **改动说明**（列出改掉了哪些 AI 腔、为什么），必要时并排 before/after 关键句。
3. 长文可写到 `outputs/humanized.md`。

## 提醒
- "AI 检测器"分数仅供参考、不可靠；本技能目标是**读起来自然且学术严谨**，不是骗检测器。
- 若原文有事实/逻辑错误，指出但不擅自"编好"。
