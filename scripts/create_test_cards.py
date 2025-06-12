#!/usr/bin/env python3
"""
测试卡片数据生成脚本

用途：
    生成测试用的知识卡片数据，通过调用 API 接口批量创建卡片。
    
使用方法：
    python scripts/create_test_cards.py [--count 20]

参数：
    --count: 可选，指定要生成的卡片数量，默认为 20
"""

import asyncio
import argparse
from typing import List
import httpx
from faker import Faker
from datetime import datetime

# 初始化 Faker，使用中文
fake = Faker(['zh_CN'])

# 预定义的主题和相关问题模板
TOPICS = {
    'Python': [
        ('什么是{concept}？', '{concept}是Python中的{feature}，主要用于{usage}。'),
        ('如何使用{concept}？', '使用{concept}的步骤如下：\n1. {step1}\n2. {step2}\n3. {step3}'),
        ('为什么需要{concept}？', '{concept}的主要作用是{purpose}，它能够{benefit}。')
    ],
    'FastAPI': [
        ('如何在FastAPI中实现{concept}？', '在FastAPI中实现{concept}需要以下步骤：\n1. {step1}\n2. {step2}'),
        ('FastAPI的{concept}有什么特点？', 'FastAPI的{concept}具有以下特点：\n1. {feature1}\n2. {feature2}'),
        ('为什么FastAPI选择{concept}？', 'FastAPI选择{concept}是因为{reason}，这样可以{benefit}。')
    ],
    'SQLAlchemy': [
        ('SQLAlchemy中的{concept}是什么？', 'SQLAlchemy的{concept}是一个{description}，用于{usage}。'),
        ('如何使用SQLAlchemy的{concept}？', '使用SQLAlchemy的{concept}的基本步骤：\n1. {step1}\n2. {step2}'),
        ('SQLAlchemy的{concept}有什么优势？', 'SQLAlchemy的{concept}提供了以下优势：\n1. {advantage1}\n2. {advantage2}')
    ],
    'MySQL': [
        ('MySQL中{concept}的作用是什么？', 'MySQL的{concept}主要用于{purpose}，它能够{function}。'),
        ('如何优化MySQL的{concept}？', '优化MySQL{concept}的方法：\n1. {method1}\n2. {method2}'),
        ('MySQL的{concept}最佳实践有哪些？', 'MySQL{concept}的最佳实践包括：\n1. {practice1}\n2. {practice2}')
    ]
}

# 每个主题的关键概念
CONCEPTS = {
    'Python': ['装饰器', '生成器', '协程', '上下文管理器', 'GIL', '元类', '描述符'],
    'FastAPI': ['依赖注入', '路由', '中间件', 'Pydantic模型', '异步支持', '参数校验'],
    'SQLAlchemy': ['会话管理', '模型关系', '查询构建', '事务控制', '连接池', '迁移系统'],
    'MySQL': ['索引优化', '事务隔离', '锁机制', '存储引擎', '分区表', '主从复制']
}

def generate_test_cards(count: int = 20) -> List[dict]:
    """
    生成测试卡片数据
    
    Args:
        count: 需要生成的卡片数量
        
    Returns:
        包含卡片数据的列表，每个卡片包含question和answer
    """
    cards = []
    topics = list(TOPICS.keys())
    
    for _ in range(count):
        # 随机选择主题和问题模板
        topic = fake.random_element(topics)
        template = fake.random_element(TOPICS[topic])
        concept = fake.random_element(CONCEPTS[topic])
        
        # 生成问题
        question = template[0].format(
            concept=concept,
            feature=fake.word(),
            usage=fake.sentence()
        )
        
        # 生成答案
        answer = template[1].format(
            concept=concept,
            feature=fake.word(),
            usage=fake.sentence(),
            purpose=fake.sentence(),
            benefit=fake.sentence(),
            step1=fake.sentence(),
            step2=fake.sentence(),
            step3=fake.sentence(),
            description=fake.sentence(),
            function=fake.sentence(),
            method1=fake.sentence(),
            method2=fake.sentence(),
            practice1=fake.sentence(),
            practice2=fake.sentence(),
            reason=fake.sentence(),
            feature1=fake.sentence(),
            feature2=fake.sentence(),
            advantage1=fake.sentence(),
            advantage2=fake.sentence()
        )
        
        cards.append({
            "question": question,
            "answer": answer
        })
    
    return cards

async def create_cards(count: int = 20):
    """
    通过API创建测试卡片
    
    Args:
        count: 要创建的卡片数量
    """
    print(f"开始创建{count}张测试卡片...")
    start_time = datetime.now()
    
    async with httpx.AsyncClient() as client:
        cards = generate_test_cards(count)
        success_count = 0
        
        for i, card in enumerate(cards, 1):
            try:
                response = await client.post(
                    'http://localhost:8001/api/v1/cards',
                    json=card,
                    timeout=10.0
                )
                if response.status_code == 200:
                    success_count += 1
                    print(f"[{i}/{count}] 成功创建卡片: {card['question'][:50]}...")
                else:
                    print(f"[{i}/{count}] 创建失败: {response.text}")
            except Exception as e:
                print(f"[{i}/{count}] 发生错误: {str(e)}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n创建完成!")
        print(f"总数: {count}")
        print(f"成功: {success_count}")
        print(f"失败: {count - success_count}")
        print(f"耗时: {duration:.2f}秒")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成测试用的知识卡片数据')
    parser.add_argument('--count', type=int, default=20, help='要生成的卡片数量（默认：20）')
    args = parser.parse_args()
    
    try:
        asyncio.run(create_cards(args.count))
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")

if __name__ == "__main__":
    main() 