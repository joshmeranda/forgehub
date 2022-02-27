import datetime

import event
from github import Github


def main():
    # todo: we need a better way to do this (storing a personal access token in plaintext is gross)
    with open("token") as token_file:
        token = token_file.read()[:-1]

    # client = Github(login_or_token=token)
    client = Github()
    client.per_page = 1000

    start_date = datetime.datetime(year=2022, month=1, day=1)
    start_date -= datetime.timedelta(days=365)

    n = event.get_calendar_event_count_after(client, start_date)

    print(n)


if __name__ == "__main__":
    main()
