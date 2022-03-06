#!/usr/bin/env python3
import events
import render
import os

from git import Driver, SshRemoteCallbacks
from github import Github


def main():
    with open("token") as token_file:
        token = token_file.readline()[:-1]

    github_client = Github(login_or_token=token)
    github_user = github_client.get_user("joshmeranda")

    print("rendering output...")
    renderer = render.TextRenderer()
    raw_data_level_map = renderer.render("BOOCHIE")

    print("retrieving user activity stats...")
    _, max_events_per_day = events.get_max_events_per_day(github_user)
    boundaries = events.get_data_level_boundaries(max_events_per_day, dilute=True)

    scaled_data_level_map = render.scale_data_level_map(boundaries, raw_data_level_map)

    home = os.getenv("HOME")
    private = os.path.join(home, ".ssh", "id_rsa")
    public = os.path.join(home, ".ssh", "id_rsa.pub")

    print("crafting commits...")
    try:
        driver = Driver(
            "forgehub-test",
            ssh="git@github.com:joshmeranda/forgehub-test.git",
            clone_callbacks=SshRemoteCallbacks(private, public),
            push_callbacks=SshRemoteCallbacks(private, public),
        )
    except Exception as err:
        print(f"error initializing repository: {err}")
        return

    driver.forge_commits(scaled_data_level_map)

    print("pushing to remote...")
    driver.push()


def test_push():
    home = os.getenv("HOME")
    private = os.path.join(home, ".ssh", "id_rsa")
    public = os.path.join(home, ".ssh", "id_rsa.pub")

    print("opening repo...")
    driver = Driver(
        "forgehub-test",
        clone_callbacks=SshRemoteCallbacks(private, public),
        push_callbacks=SshRemoteCallbacks(private, public),
    )

    print("pushing to remote...")
    driver.push()


def test_render():
    print("rendering...")
    renderer = render.TextRenderer()
    renderer.render("ABC")


if __name__ == "__main__":
    main()
