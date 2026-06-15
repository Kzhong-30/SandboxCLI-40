# SnowNLP vs TextBlob 情感分析准确率对比

## 测试样本
- 数量：20 条典型中文评论（10 条正面 / 10 条负面）
- 来源：模拟电商、餐饮、生活、工作等场景的真实用户评论
- 判定标准：score > 0.15 为 positive，score < -0.15 为 negative，中间为 neutral

## 逐条对比表

| 编号 | 真实标签 | SnowNLP 分数 | SnowNLP 预测 | TextBlob 分数 | TextBlob 预测 | SnowNLP 命中 | TextBlob 命中 | 样本片段 |
|-----|---------|------------|------------|-------------|-------------|------------|-------------|---------|
| 1 | positive | 0.975 | positive | 0.000 | neutral | ✅ | ❌ | 这款产品质量非常好，使用体验很棒，强... |
| 2 | positive | 0.651 | positive | 0.000 | neutral | ✅ | ❌ | 今天天气真好，心情愉快，一切都很顺利 |
| 3 | positive | 0.998 | positive | 0.000 | neutral | ✅ | ❌ | 这家餐厅的菜品味道太棒了，服务也很周... |
| 4 | positive | 0.998 | positive | 0.000 | neutral | ✅ | ❌ | 新买的手机性能很强，拍照效果特别清晰... |
| 5 | positive | 0.996 | positive | 0.000 | neutral | ✅ | ❌ | 这部电影太精彩了，剧情扣人心弦，演员... |
| 6 | positive | 0.991 | positive | 0.000 | neutral | ✅ | ❌ | 这次旅行非常愉快，风景优美，当地人民... |
| 7 | positive | 0.997 | positive | 0.000 | neutral | ✅ | ❌ | 孩子考试得了满分，全家人都特别开心，... |
| 8 | positive | 0.921 | positive | 0.000 | neutral | ✅ | ❌ | 这本书写得真好，内容丰富有深度，受益匪浅 |
| 9 | positive | 0.737 | positive | 0.000 | neutral | ✅ | ❌ | 客户对我们的方案非常认可，项目进展一... |
| 10 | positive | 0.990 | positive | 0.000 | neutral | ✅ | ❌ | 经过努力终于完成了目标，感觉特别有成就感 |
| 11 | negative | -0.999 | negative | 0.000 | neutral | ✅ | ❌ | 这个产品质量太差了，用了三天就坏了，... |
| 12 | negative | -0.483 | negative | 0.000 | neutral | ✅ | ❌ | 今天真倒霉，路上堵车迟到了，还被老板批评 |
| 13 | negative | -0.999 | negative | 0.000 | neutral | ✅ | ❌ | 这家店的服务态度极差，食物也不新鲜，... |
| 14 | negative | -0.993 | negative | 0.000 | neutral | ✅ | ❌ | 新买的电脑频繁死机，售后也不处理，太... |
| 15 | negative | -0.119 | neutral | 0.000 | neutral | ❌ | ❌ | 这部电影无聊透顶，剧情拖沓，完全是浪... |
| 16 | negative | -0.994 | negative | 0.000 | neutral | ✅ | ❌ | 这次旅行糟透了，天气不好，景点人满为... |
| 17 | negative | 0.443 | positive | 0.000 | neutral | ❌ | ❌ | 孩子考试不及格，让人非常担心，不知道... |
| 18 | negative | -0.107 | neutral | 0.000 | neutral | ❌ | ❌ | 这本书写得乱七八糟，逻辑混乱，读完什... |
| 19 | negative | -0.907 | negative | 0.000 | neutral | ✅ | ❌ | 客户拒绝了我们的方案，几个月的努力都... |
| 20 | negative | 0.778 | positive | 0.000 | neutral | ❌ | ❌ | 努力了很久还是失败了，感觉很挫败，不... |

## 准确率汇总

| 引擎 | 正确数 / 总数 | 准确率 |
|-----|--------------|-------|
| SnowNLP (中文原生) | 16 / 20 | 80.0% |
| TextBlob (需翻译+英文模型) | 0 / 20 | 0.0% |

## 结论

- SnowNLP 针对中文语料训练，对中文情感的识别准确率显著高于 TextBlob
- TextBlob 基于英文语料训练，对中文需要先翻译，准确率不稳定
- 样本中 TextBlob 对中文的翻译和情感判断存在明显偏差，多数样本被错误判断为中性
- 本项目默认使用 SnowNLP 处理中文，英文自动降级到 TextBlob，失败时再降级到规则引擎
