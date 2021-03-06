from .cache import like_cache, article_cache, rate_cache, comment_cache, notify_cache
from .models import Article, Comment
from front.models import FrontUser, Rate, Like, Notification
from common.exceptions import *
from exts import db, scheduler
from functools import wraps
from datetime import datetime, timedelta
import json
import time
import heapq


class logger():
    def __init__(self, info):
        self.info = info

    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            try:
                print("*" * 10)
                print("开始【{}】...".format(self.info))
                t1 = time.time()
                with scheduler.app.app_context():
                    count = func(*args, **kwargs)
                t2 = time.time()
                print("【{}】执行完毕...总耗时【{:.3f}】s...一共更新了【{}】条数据...".format(self.info, t2 - t1, count))
                print("*" * 10)
            except (ConnectionError, TimeoutError):
                print("缓存炸了")
            except OperationalError:
                print("数据库炸了")
        return inner


@logger(info="保存文章浏览量数据")
def save_views():
    count = 0
    views = article_cache.get("views")
    article_cache.delete("views")
    for article_id, view in views.items():
        article = Article.query.get(article_id)
        if article:
            article.views += int(view)
            count += 1
    db.session.commit()
    return count


@logger(info="保存文章点赞数据")
def save_likes():
    queue = like_cache.get("queue")
    like_cache.delete("queue")
    count = 0
    for like_id, value in queue.items():
        value = json.loads(value)
        like = Like.query.get(like_id)
        if like:
            like.status = value["status"]
            count += 1
        elif value["status"]:
            article_id, user_id, created = value["id"], value["user_id"], datetime.fromtimestamp(value["created"])
            article = Article.query.get(article_id)
            if article:
                user = FrontUser.query.get(user_id)
                if user:
                    like = Like(created=created)
                    like.user = user
                    like.article = article

                    if user.id != article.author_id:
                        notification = Notification(category=1, link_id=article_id,
                                                    sender_content="赞了你的帖子", acceptor_content=article.title)
                        notification.acceptor = article.author
                        notification.sender = user
                        db.session.add(notification)
                        article.author.notification_increase(notify_cache)

                    db.session.add(like)
                    count += 1
    db.session.commit()
    return count


@logger(info="保存评论点赞数据")
def save_rates():
    queue = rate_cache.get("queue")
    rate_cache.delete("queue")
    count = 0
    for rate_id, value in queue.items():
        value = json.loads(value)
        rate = Rate.query.get(rate_id)
        if rate:
            rate.status = value["status"]
            count += 1
        elif value["status"]:
            comment_id, user_id, created = value["id"], value["user_id"], datetime.fromtimestamp(value["created"])
            comment = Comment.query.get(comment_id)
            if comment:
                user = FrontUser.query.get(user_id)
                if user:
                    rate = Rate(created=created)
                    rate.user = user
                    rate.comment = comment

                    if user.id != comment.author_id:
                        notification = Notification(category=2, link_id=comment_id,
                                                    sender_content="赞了你的评论", acceptor_content=comment.content)
                        notification.acceptor = comment.author
                        notification.sender = user
                        db.session.add(notification)
                        comment.author.notification_increase(notify_cache)

                    db.session.add(rate)
                    count += 1
    db.session.commit()
    return count


@logger(info="计算热帖排行")
def calculator_article_score():
    # 暂时定十五天内的帖子
    now = datetime.now()
    t1 = time.time()
    articles = Article.query.filter(Article.created >= now - timedelta(days=100), Article.status == 1).all()
    score = {article.id: article.calculate_score(now) for article in articles}
    t2 = time.time()
    print("搜索数据库耗时: {:.3f}".format(t2 - t1))
    t1 = time.time()
    hot_articles = heapq.nlargest(10, score, key=lambda item: score[item])
    t2 = time.time()
    print("堆排序耗时: {:.3f}".format(t2 - t1))
    article_cache.set_pointed("hot", "rank", hot_articles, json=True, permanent=True)
    return len(score)
