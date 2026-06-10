import random
import uuid
from datetime import datetime
from typing import List, Dict


class CrawlerService:
    WEIBO_TEMPLATES = [
        "{keyword}真的太棒了！我每天都在用，强烈推荐给大家！",
        "最近买了{keyword}，体验真的很一般，希望能改进一下。",
        "{keyword}新品发布啦，大家觉得怎么样？期待评测！",
        "用了{keyword}三个月，说说我的真实感受...整体来说还是不错的。",
        "{keyword}这波操作太绝了，必须支持！",
        "吐槽一下{keyword}，售后服务真的让人失望。",
        "今天分享{keyword}的使用技巧，记得收藏哦～",
        "有人跟我一样喜欢{keyword}的吗？举个手！",
        "{keyword}最近问题好多啊，官方能不能回应一下？",
        "终于等到{keyword}更新了，希望修复了之前的bug。",
    ]

    NEWS_TEMPLATES = [
        "{keyword}发布2024年度战略规划，将投入10亿用于技术研发",
        "{keyword}市场份额持续增长，稳居行业第一梯队",
        "{keyword}遭遇信任危机，多个合作伙伴宣布暂停合作",
        "深度解析：{keyword}为何能在激烈竞争中脱颖而出",
        "{keyword}完成新一轮融资，估值突破百亿",
        "{keyword}产品质量问题频发，消费者投诉量激增",
        "独家专访：{keyword}CEO谈未来发展方向",
        "{keyword}与多家知名企业达成战略合作，共建生态",
        "监管部门约谈{keyword}，要求整改相关问题",
        "{keyword}发布创新产品，引领行业新趋势",
    ]

    FORUM_TEMPLATES = [
        "关于{keyword}的使用心得，欢迎大家一起讨论",
        "{keyword}值得入手吗？求真实用户回答",
        "发现{keyword}一个隐藏功能，太实用了！",
        "{keyword}的竞争对手越来越多，还能保持优势吗？",
        "求问：{keyword}出现这个问题怎么办？急！",
        "用了这么久{keyword}，总结下优缺点",
        "{keyword}官方论坛的活动太棒了，福利多多",
        "为什么我觉得{keyword}没有网上说的那么好？",
        "分享一个{keyword}的优化方案，亲测有效",
        "大家预测下{keyword}接下来会有什么大动作？",
    ]

    AUTHORS = [
        "科技达人小王", "产品经理小李", "数码爱好者", "用户A",
        "资深评测师", "匿名用户", "行业观察家", "财经博主",
        "普通消费者", "技术极客", "营销专家", "数据分析师",
    ]

    @classmethod
    def _get_templates(cls, source_type: str) -> List[str]:
        if source_type == "weibo":
            return cls.WEIBO_TEMPLATES
        elif source_type == "news":
            return cls.NEWS_TEMPLATES
        elif source_type == "forum":
            return cls.FORUM_TEMPLATES
        return cls.WEIBO_TEMPLATES

    @classmethod
    def generate_content(
        cls,
        keyword: str,
        source_type: str,
        count: int = 5
    ) -> List[Dict]:
        templates = cls._get_templates(source_type)
        results = []

        for _ in range(count):
            template = random.choice(templates)
            content = template.format(keyword=keyword)
            author = random.choice(cls.AUTHORS)

            post_id = str(uuid.uuid4())[:8]
            if source_type == "weibo":
                url = f"https://weibo.com/{post_id}"
            elif source_type == "news":
                url = f"https://news.example.com/article/{post_id}"
            else:
                url = f"https://forum.example.com/thread/{post_id}"

            results.append({
                "source_type": source_type,
                "title": f"{keyword} - {source_type.upper()}内容",
                "content": content,
                "author": author,
                "url": url,
                "raw_data": {
                    "post_id": post_id,
                    "likes": random.randint(0, 10000),
                    "comments": random.randint(0, 500),
                    "shares": random.randint(0, 2000),
                    "views": random.randint(100, 100000),
                    "collected_at": datetime.utcnow().isoformat(),
                }
            })

        return results

    @classmethod
    def crawl_monitor(
        cls,
        keywords: List[str],
        sources: List[str],
        per_keyword_count: int = 3
    ) -> List[Dict]:
        all_data = []
        for keyword in keywords:
            for source in sources:
                data = cls.generate_content(keyword, source, per_keyword_count)
                all_data.extend(data)
        return all_data
