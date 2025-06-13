"""
复习策略管理模块
定义不同的复习间隔计算策略
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List
from pydantic import BaseModel


class IntervalRule(BaseModel):
    """
    间隔规则模型
    
    属性:
        min_count: 最小复习次数（包含）
        max_count: 最大复习次数（包含）
        days: 间隔天数
    """
    min_count: int
    max_count: int
    days: int


class ReviewStrategy:
    """
    复习策略基类
    可以继承此类实现不同的复习策略
    """
    
    def calculate_next_review_time(self, review_count: int) -> datetime:
        """
        计算下次复习时间
        
        参数:
            review_count: 当前复习次数
            
        返回:
            datetime: 下次复习时间
        """
        raise NotImplementedError


class DefaultReviewStrategy(ReviewStrategy):
    """
    默认的复习策略实现
    基于固定的间隔规则
    """
    
    def __init__(self):
        # 定义间隔规则
        self.rules: List[IntervalRule] = [
            IntervalRule(min_count=1, max_count=3, days=1),   # 1-3次：1天
            IntervalRule(min_count=4, max_count=4, days=2),   # 第4次：2天
            IntervalRule(min_count=5, max_count=5, days=3),   # 第5次：3天
            IntervalRule(min_count=6, max_count=6, days=5),   # 第6次：5天
            IntervalRule(min_count=7, max_count=8, days=7),   # 7-8次：7天
            IntervalRule(min_count=9, max_count=10, days=14), # 9-10次：14天
            IntervalRule(min_count=11, max_count=12, days=30),# 11-12次：30天
            IntervalRule(min_count=13, max_count=999, days=60)# 13次以上：60天
        ]
    
    def calculate_next_review_time(self, review_count: int) -> datetime:
        """
        根据复习次数计算下次复习时间
        
        参数:
            review_count: 当前复习次数
            
        返回:
            datetime: 下次复习时间
        """
        # 查找适用的规则
        for rule in self.rules:
            if rule.min_count <= review_count <= rule.max_count:
                return datetime.now(timezone.utc) + timedelta(days=rule.days)
        
        # 如果没有找到匹配的规则（不应该发生），使用默认间隔
        return datetime.now(timezone.utc) + timedelta(days=1)


class ConfigurableReviewStrategy(ReviewStrategy):
    """
    可配置的复习策略
    间隔规则可以通过配置文件或环境变量设置
    """
    
    def __init__(self, rules: List[Dict[str, int]]):
        """
        初始化可配置的复习策略
        
        参数:
            rules: 间隔规则列表，每个规则是一个字典，包含：
                  - min_count: 最小复习次数
                  - max_count: 最大复习次数
                  - days: 间隔天数
        """
        self.rules = [IntervalRule(**rule) for rule in rules]
        # 确保规则按照 min_count 排序
        self.rules.sort(key=lambda x: x.min_count)
    
    def calculate_next_review_time(self, review_count: int) -> datetime:
        """
        根据复习次数计算下次复习时间
        间隔是累加的，而不是每次都从当前时间开始计算
        
        参数:
            review_count: 当前复习次数
            
        返回:
            datetime: 下次复习时间
        """
        # 计算从第一次复习开始的总间隔天数
        total_days = 0
        for i in range(1, review_count + 1):
            # 查找当前复习次数对应的规则
            for rule in self.rules:
                if rule.min_count <= i <= rule.max_count:
                    total_days += rule.days
                    break
            else:
                # 如果没有找到匹配的规则，使用最后一个规则
                if self.rules:
                    total_days += self.rules[-1].days
                else:
                    total_days += 1
        
        # 返回第一次复习时间加上总间隔天数
        return datetime.now(timezone.utc) + timedelta(days=total_days)


# 创建默认的复习策略实例
default_strategy = DefaultReviewStrategy() 