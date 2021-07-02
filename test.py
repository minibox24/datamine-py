import requests
import re
import discord
from dateutil import parser

regexs = {
    "build_number": re.compile(r"(Canary\sbuild:\s([0-9]*))"),
    "markdown": re.compile(r'!\[.*\]\((.*?)\s*("(?:.*[^"])")?\s*\)'),
    "html": re.compile(r'<img\s+[^>]*src="([^"]*)"[^>]*>'),
}

headers = {"Authorization": "token"}


def parse_build_number(message):
    return int(regexs["build_number"].findall(message)[0][1])


def inject_build_number(data):
    data["commit"]["build_number"] = parse_build_number(data["commit"]["message"])
    return data


def get_commits_with_comments():
    return sorted(
        map(
            inject_build_number,
            filter(
                lambda x: x["commit"]["comment_count"] >= 1,
                requests.get(
                    "https://api.github.com/repos/Discord-Datamining/Discord-Datamining/commits",
                    headers=headers,
                ).json(),
            ),
        ),
        key=lambda x: x["commit"]["build_number"],
        reverse=True,
    )


def parse_images_from_comment(comment):
    images = []

    markdowns = list(regexs["markdown"].finditer(comment["body"]))
    htmls = list(regexs["html"].finditer(comment["body"]))

    if markdowns:
        for i in markdowns:
            images.append(
                {
                    "old": i.group(),
                    "new": i.groups()[0],
                }
            )

    if htmls:
        for i in htmls:
            images.append(
                {
                    "old": i.group(),
                    "new": i.groups()[0],
                }
            )

    return images


def get_comments_with_images_of_commit(commit):
    def process(comment):
        images = parse_images_from_comment(comment)

        if len(images) >= 1:
            for i in images:
                comment["body"] = comment["body"].replace(i["old"], "")

        comment["images"] = images
        return comment

    comments = list(
        map(process, requests.get(commit["comments_url"], headers=headers).json())
    )
    return [commit["commit"], comments]


def transform_comment_data_shape(comment, title, build_number):
    return {
        "id": comment["id"],
        "title": title,
        "build_number": build_number,
        "timestamp": parser.parse(comment["created_at"]),
        "url": comment["html_url"],
        "description": comment["body"],
        "images": list(map(lambda x: x["new"], comment["images"])),
        "user": {
            "username": comment["user"]["login"],
            "avatar_url": comment["user"]["avatar_url"],
            "url": comment["user"]["url"],
            "id": comment["user"]["id"],
        },
    }


commits = get_commits_with_comments()
commits_with_comments = list(map(get_comments_with_images_of_commit, commits))

for commit, comments in commits_with_comments:
    for comment in comments:
        data = transform_comment_data_shape(
            comment, commit["message"], commit["build_number"]
        )

        image_queue = []

        embed = discord.Embed()
        embed.color = discord.Color.blurple()
        embed.title = data["title"]
        embed.description = (
            data["description"][:4000] + "..."
            if len(data["description"]) > 4000
            else data["description"]
        )
        embed.url = data["url"]
        embed.timestamp = data["timestamp"]

        embed.set_author(
            name=data["user"]["username"],
            icon_url=data["user"]["avatar_url"],
            url=data["user"]["url"],
        )

        if len(data["images"]) > 0:
            embed.set_image(url=data["images"][0])
            if len(data["images"]) > 1:
                image_queue = data["images"][1:]

        webhook = discord.Webhook.from_url(
            "",
            adapter=discord.RequestsWebhookAdapter(requests.Session()),
        )
        webhook.send(embed=embed)

        for i in image_queue:
            webhook.send(i)
