from datetime import datetime, timezone
from app.core.review_strategy import ConfigurableReviewStrategy
from app.core.config import settings

def test_strategy():
    strategy = ConfigurableReviewStrategy(settings.REVIEW_STRATEGY_RULES)
    print("复习次数\t应间隔(天)\t实际间隔(天)\t下次复习时间")
    now = datetime.now(timezone.utc)
    for review_count in range(1, 20):
        next_time = strategy.calculate_next_review_time(review_count)
        delta_days = (next_time - now).days
        print(f"{review_count}\t\t{get_expected_days(review_count)}\t\t{delta_days}\t\t{next_time.isoformat()}")

def get_expected_days(count):
    # 这里和 config.py 里的规则保持一致
    rules = [
        (1, 3, 1),
        (4, 4, 2),
        (5, 5, 3),
        (6, 6, 5),
        (7, 8, 7),
        (9, 10, 14),
        (11, 12, 30),
        (13, 999, 60)
    ]
    for min_c, max_c, days in rules:
        if min_c <= count <= max_c:
            return days
    return rules[-1][2]

if __name__ == "__main__":
    test_strategy() 