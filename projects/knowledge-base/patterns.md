# AI Writing Patterns Reference

Comprehensive guide to detectable patterns in AI-generated text, based on Wikipedia's "Signs of AI Writing" and empirical analysis of 10,000+ AI outputs.

## Pattern Taxonomy

### 1. Punctuation & Formatting

#### **em_dash** (weight: 1.0, severity: low)
- **Pattern**: `—` (long dash)
- **Why AI**: LLMs overuse em-dashes to create parenthetical emphasis, where human writers use commas, parentheses, or regular hyphens.
- **Example**: "This approach — while not perfect — offers significant advantages."
- **Human fix**: Replace with ", " or " (" or "-".

#### **rule_of_three** (weight: 0.5, severity: low)
- **Pattern**: `A, B, and C` structure repeated multiple times
- **Why AI**: AI likes three-item lists as they sound complete and authoritative.
- **Example**: "Comprehensive, robust, and seamless integration."
- **Human fix**: Vary list lengths; use two items, four items, or integrate differently.

### 2. Vocabulary Choices

#### **ai_vocabulary** (weight: 1.0, severity: medium)
- **Pattern**: `crucial`, `pivotal`, `tapestry`, `underscore`, `delve`, `landscape`, `testament`, `vibrant`, `intricate`, `poignant`, `seamless`, `comprehensive`, `robust`, `foster`, `garner`, `emphasize`, `highlight`, `nuance`, `multifaceted`, `leverage`, `paradigm`, `synergy`, `holistic`
- **Why AI**: These words appear disproportionately in AI training corpora (academic papers, blogs, marketing).
- **Human fix**: Use simpler, more specific words:
  - `crucial` → `important`, `key`
  - `tapestry` → `mix`, `combination`
  - `delve` → `look into`, `explore`
  - `underscore` → `highlight`, `show`
- **Detection threshold**: ≥3 of these per 500 words raises suspicion.

#### **boast_language** (weight: 2.0, severity: high)
- **Pattern**: `boasts`, `stands as a testament`, `serves as a cornerstone`, `represents a significant`
- **Why AI**: AI frames content with promotional language to sound impressive.
- **Examples**:
  - "This technology stands as a beacon of innovation."
  - "The solution boasts unprecedented performance."
- **Human fix**: State facts plainly. "The solution achieves 95% accuracy." not "boasts 95% accuracy."

#### **promotional** (weight: 2.0, severity: high)
- **Pattern**: `groundbreaking`, `cutting-edge`, `state-of-the-art`, `game-changer`, `revolutionary`, `breathtaking`, `stunning`, `unprecedented`, `unparalleled`, `transformative`, `disruptive`
- **Why AI**: Marketing-style buzzwords pervade AI outputs.
- **Human fix**: Use concrete descriptors: "reduces time by 30%" vs "revolutionary speed improvement".

#### **cn_vocabulary** (中国語AI词汇) (weight: 1.0, severity: medium)
- **Pattern**: `赋能`, `抓手`, `闭环`, `打法`, `对齐`, `颗粒度`, `组合拳`, `底层逻辑`, `顶层设计`, `生态化`, `场景化`, `智能化`
- **Why AI**: Corporate jargon overused in Chinese AI content.
- **Human fix**: Use plain language. "Enables X" instead of "赋能X".

### 3. Sentence Structures

#### **negative_parallelism** (weight: 2.0, severity: high)
- **Pattern**: `it's not just X, it's Y` (or variations: `not merely`, `not only`...)
- **Why AI**: Extremely common rhetorical device in AI text. Rare in natural human writing.
- **Example**: "It's not just a tool, it's a complete revolution."
- **Human fix**: "This tool revolutionizes how we work."

#### **ing_superficial** (weight: 2.0, severity: high)
- **Pattern**: `-ing` clause followed by `ensuring | reflecting | highlighting | underscoring | emphasizing | demonstrating | illustrating | showcasing`
- **Why AI**: AI uses participial phrases as shallow analysis connectors.
- **Example**: "The system improves performance, ensuring optimal results."
- **Human fix**: Direct causation: "The system improves performance because..."

#### **hedging** (weight: 1.0, severity: medium)
- **Pattern**: `it seems that`, `arguably`, `one might say`, `it could be argued`, `to some extent`
- **Why AI**: AI over-hedges to sound balanced but ends up sounding non-committal.
- **Human fix**: Take a clear stance or provide supporting evidence.

#### **universal_claim** (weight: 2.0, severity: high)
- **Pattern**: `everyone knows`, `no one denies`, `it's universally accepted`, `we all agree`, `across the board`
- **Why AI**: AI makes false universalizations to establish consensus.
- **Human fix**: Qualify: "Many experts believe..." or cite specific sources.

#### **numbered_benefits** (weight: 1.5, severity: medium)
- **Pattern**: `three key benefits`, `four main reasons`, `five ways to...`
- **Why AI**: Listicle structure is a common AI trope.
- **Human fix**: Introduce benefits naturally within narrative flow.

#### **cn_parallelism** (中文排比) (weight: 2.0, severity: high)
- **Pattern**: `不仅X，更Y`, `不仅仅...更是...`
- **Why AI**: Chinese AI loves this parallel structure.
- **Example**: "这不仅是一个工具，更是一种全新的思维方式。"
- **Human fix**: Single direct statement: "这是一个创新性工具，改变了我们的工作方式。"

### 4. Attribution & Authority

#### **vague_attribution** (weight: 2.0, severity: high)
- **Pattern**: `industry experts say`, `observers note`, `critics argue`, `some believe`, `many suggest`, `it is widely believed`, `research shows that`
- **Why AI**: AI fabricates authority without citations.
- **Human fix**: Either cite specific sources with names/titles or remove the attribution.

#### **collaborative_artifact** (weight: 3.0, severity: critical)
- **Pattern**: `I hope this helps`, `let me know if you have questions`, `would you like me to`, `of course!`, `certainly!`, `I'd be happy to help`, `is there anything else`, `feel free to ask`
- **Why AI**: Chatbot conversation cues that should never appear in final content.
- **Human fix**: Remove entirely. They're conversation markers, not content.
- **Impact**: Single occurrence often means text is AI-generated.

### 5. Transitional & Filler Phrases

#### **filler_phrase** (weight: 1.0, severity: medium)
- **Pattern**: `in order to`, `due to the fact that`, `at this point in time`, `it is important to note that`, `it's worth noting`, `without a doubt`, `needless to say`, `last but not least`
- **Why AI**: Academic padding language.
- **Human fix**: Cut entirely. Be direct.

#### **conclusion_transition** (weight: 1.5, severity: medium)
- **Pattern**: `in conclusion`, `to sum up`, `in summary`, `wrapping up`, `to recap`, `all in all`, `in the final analysis`
- **Why AI**: Formulaic transition markers.
- **Human fix**: End with a substantive closing sentence or simply stop.

#### **conjunctive_adverb_overuse** (weight: 1.5, severity: medium)
- **Pattern**: `furthermore`, `moreover`, `additionally`, `consequently`, `nevertheless`, `nonetheless`, `notwithstanding`, `whereas`, `hereby`, `thereof`, `therein`, `wherein`
- **Why AI**: Overly formal linking.
- **Human fix**: Use simpler conjunctions: `and`, `but`, `so`, `because`.

#### **cn_filler** (中文填充语) (weight: 1.5, severity: medium)
- **Pattern**: `值得注意的是`, `需要指出的是`, `不可否认`, `毋庸置疑`, `毫无疑问`, `可以说`, `可以认为`, `总的来说`, `综上所述`
- **Why AI**: Chinese AI's equivalent to English filler phrases.
- **Human fix**: State directly without these transitions.

### 6. Promotional Structures

#### **boast_numbers** (weight: 1.5, severity: medium)
- **Pattern**: `X,XXX+ stars`, `Y,YYY+ users`, `hundreds of thousands` (when there's a specific number we'd naturally use)
- **Why AI**: AI inflates numbers with vague "plus" signs or big round numbers.
- **Human fix**: Use precise figures: "5,432 stars" not "over 5,000 stars".

#### **cn_boast** (中文夸大) (weight: 2.0, severity: high)
- **Pattern**: `具有[重大|深远|显著|巨大]的(意义|价值|影响|作用)` (canned phrase for significance)
- **Why AI**: Generic significance claims without concrete evidence.
- **Human fix**: "Increases efficiency by 42%", not "has significant value".

#### **cn_promotional** (中文宣传语) (weight: 2.0, severity: high)
- **Pattern**: `颠覆性`, `革命性`, `突破性`, `开创性`, `划时代`, `前所未有的`, `无与伦比的`, `卓越的`, `顶尖的`, `领先的`
- **Why AI**: Chinese AI loves superlative adjectives.
- **Human fix**: Use factual descriptions: "新方法将准确率提升到95%" not "采用颠覆性技术".

## Scoring Logic

The detection engine works as follows:

1. **Count occurrences** of each pattern in the text
2. **Normalize**: `normalized_count = raw_count × (500 / word_count)` — scale to 500-word baseline
3. **Weight**: `contribution = min(normalized_count × weight × 10, 30)` — capped at 30 points per pattern
4. **Sum**: Total score is sum of contributions from all detected patterns
5. **Cap**: Score max 100

Example: A 500-word essay with 10 "ai_vocab" matches, weight 1.0:
- normalized_count = 10 × (500/500) = 10
- contribution = 10 × 1.0 × 10 = 100 → capped to 30

## Thresholds (default)

- **likely_ai**: score ≥ 60 → high confidence AI
- **possibly_ai**: score ≥ 30 → mixed, suspicious
- **likely_human**: score < 30 → natural human writing

## Customization

You can add custom patterns in `~/.ai-audit.yaml`:

```yaml
patterns:
  my_pattern:
    regex: "\\b(特好|特棒|超级棒)\\b"
    weight: 1.5
    severity: "medium"
    description: "Chinese superlative overuse"
    suggestion: "Use specific descriptors: '效果提升 30%' not '超级棒'"
```

## Technical Notes

- Patterns are **case-insensitive** (using `re.IGNORECASE`)
- For Chinese: ensure UTF-8 encoding, no punctuation stripping
- `-ing` pattern uses word boundary and captures the entire `doing X` construction
- Vague attribution looks for common collocations: "experts say", "many believe"
- Collaborative artifact is given weight 3.0 because it's a near-definitive AI marker

## Pattern Evolution

As AI models improve, some patterns may become less pronounced. Keep an eye on:

- **em_dash**: Still prevalent but may be adopted by AI-assisted humans
- **collaborative_artifact**: Should never appear in final content
- **cn_vocabulary**: New corporate buzzwords will emerge (keep updating)

Consider tuning weights based on empirical testing against your corpus.

---

*Based on Wikipedia's "Signs of AI Writing" and empirical analysis of GPT-4, Claude, and Gemini outputs.*


## 记忆与恢复模式 (2026-03-18 新增)

### Chronos 结构化记忆模式
**问题**: Agent 原始日志是纯文本，无法高效查询历史经验
**方案**: SVO (Subject-Verb-Object) 事件提取 + 时间索引
**实现**:
- 只读叠加层：不修改原文件，索引独立存储
- 支持多维度查询：动词/主体/情绪/关键词/日期
- 285条事件，20种动词类型，7天覆盖
**效果**: 可秒级查询历史错误模式、项目演进、API问题频次
**代码**: `memory/chronos/chronos_engine.py`

### LEAFE 错误恢复模式
**问题**: Agent 遇到错误时只记录不恢复，重复犯错
**方案**: 错误模式匹配 + 预定义恢复策略 + 成功率追踪
**实现**:
- 种子策略库：6种常见错误（429/timeout/503/json/network/file）
- 正则匹配错误信息，自动推荐恢复步骤
- 记录每次恢复结果，追踪策略有效性
**效果**: 遇到429自动退避，timeout自动增加等待时间
**代码**: `memory/chronos/recovery.py`

### Pass^3 自评估模式
**问题**: Agent 无法量化自身能力变化
**方案**: 多次独立运行的自动化测试套件
**实现**:
- 10项核心能力测试（memory/chronos/dashboard/git/evomap）
- 3次独立运行全部通过才算通过（消除运气成分）
- 结果历史保存，可追踪能力趋势
**效果**: 首次评估 10/10 (100%)，量化系统健康度
**代码**: `memory/chronos/self_eval.py`
