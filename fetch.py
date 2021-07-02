import re
import aiohttp
from dateutil import parser

regexs = {
    "build_number": re.compile(r"(Canary\sbuild:\s([0-9]*))"),
    "markdown": re.compile(r'!\[.*\]\((.*?)\s*("(?:.*[^"])")?\s*\)'),
    "html": re.compile(r'<img\s+[^>]*src="([^"]*)"[^>]*>'),
}


async def request(url, token):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"Authorization": f"token {token}"}) as res:
            return await res.json()


def parse_build_number(message):
    return int(regexs["build_number"].findall(message)[0][1])


def inject_build_number(data):
    data["commit"]["build_number"] = parse_build_number(data["commit"]["message"])
    return data


async def get_commits_with_comments(token):
    return sorted(
        map(
            inject_build_number,
            filter(
                lambda x: x["commit"]["comment_count"] >= 1,
                await request(
                    "https://api.github.com/repos/Discord-Datamining/Discord-Datamining/commits",
                    token,
                ),
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


async def get_comments_with_images_of_commit(token, commit):
    def process(comment):
        images = parse_images_from_comment(comment)

        if len(images) >= 1:
            for i in images:
                comment["body"] = comment["body"].replace(i["old"], "")

        comment["images"] = images
        return comment

    comments = list(map(process, await request(commit["comments_url"], token)))
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


async def fetch(token):
    commits = await get_commits_with_comments(token)
    commits_with_comments = [
        await get_comments_with_images_of_commit(token, commit) for commit in commits
    ]

    for commit, comments in commits_with_comments:
        for comment in comments:
            return transform_comment_data_shape(
                comment, commit["message"], commit["build_number"]
            )
