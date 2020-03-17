import time

import requests
import datetime
import yaml

config_file = open('config.yaml', 'r')
with config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)
    forum_url = config['forum_url']
    username = config['username']
    icon_url = config['icon_url']
    webhook_url = config['webhook_url']

new_topics = {}


def build_message(topic):
    op_timestamp = datetime.datetime.strptime(topic["created_at"], '%Y-%m-%dT%H:%M:%S.%fZ')
    is_new = op_timestamp.date() >= (datetime.datetime.today() - datetime.timedelta(3)).date()

    if topic['posts_count'] > 1 and is_new:
        topic_data = requests.get(f"{forum_url}/t/{topic['id']}.json")
        topic_posts = topic_data.json()['post_stream']['posts']

        op_post_request = requests.get(f"{forum_url}/posts/{topic_posts[0]['id']}.json")
        op_post = op_post_request.json()

        op_username = "Thread Creator"
        op_avatar = str(op_post['avatar_template']).replace("{size}", "200")

        if topic_posts:
            if op_post['name'] != '':
                op_username = op_post['name']
            else:
                op_username = op_post['username']

        post_content = op_post['raw']

        ret_dict = dict(username=username,
                        icon_url=icon_url,
                        attachments=[dict(
                            author_name=op_username,
                            author_icon=op_avatar,
                            # uncomment if you want to have a preview of the posts content inside the bot posts
                            # text=f"{post_content[:300]}...",
                            title=topic['title'],
                            title_link=f"{forum_url}/t/{topic['slug']}/{topic['id']}",
                            image_url=topic['image_url'],
                            fields=[
                                {
                                    "short": True,
                                    "title": "Created",
                                    "value": f"On {op_timestamp.strftime('%A %d. %B %Y at %H:%M')}"
                                },
                            ],
                        )],
                        props=dict(card=post_content)
                        )
        return ret_dict, True
    return {}, False


def decode():
    r = requests.get(f'{forum_url}/latest.json')
    try:
        latest = r.json()
        latest = latest['topic_list']['topics']
    except ValueError:
        return [], False
    return latest, True


def generate_posts():
    topics = decode()
    num_topics = 0
    if not topics:
        return "Unable to generate"
    for topic in topics[0]:
        msg = build_message(topic)
        if msg[1]:
            if topic['id'] not in new_topics:
                r = requests.post(webhook_url, json=msg[0])
                print(r.text)
                new_topics[topic['id']] = True
                num_topics += 1
    return num_topics


def get_latest():
    num_posts = generate_posts()
    bot_fin_msg = dict(
        text=f"Went back up until 3 days ago and got {num_posts} new topics.",
        username=username,
        icon_url=icon_url
    )
    requests.post(webhook_url, json=bot_fin_msg)
    return f"Went back up until 3 days ago and got {num_posts} new topics."


def main():
    while True:
        print("Getting latest posts.")
        print(f"Waiting {config['sleep_time'] / 60} Minutes until next fetch.")
        time.sleep(config['sleep_time'])


main()
