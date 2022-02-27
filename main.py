import events

from github import Github


def main():
    # todo: we need a better way to do this (storing a personal access token in plaintext is gross)
    with open("token") as token_file:
        token = token_file.read()[:-1]

    client = Github(login_or_token=token)

    print(f"Fetching events...")

    (d, n) = events.get_max_events_per_day(client, "joshmeranda")

    print(d, n)


if __name__ == "__main__":
    main()
