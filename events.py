from collections import defaultdict
from datetime import date
from enum import Enum

from github import Event, Github


class __EventType(str, Enum):
    """Constant for even type names.

     Taken from github docs:
        https://docs.github.com/en/developers/webhooks-and-events/events/github-event-types#gollumevent
    """

    COMMIT_COMMENT = "CommitCommentEvent"

    CREATE = "CreateEvent"

    DELETE = "DeleteEvent"

    FORK = "ForkEvent"

    GOLLUM = "GollumEvent"

    ISSUE_COMMENT = "IssueCommentEvent"

    ISSUE = "IssuesEvent"

    MEMBER = "MemberEvent"

    PUBLIC = "PublicEvent"

    PULL_REQUEST = "PullRequestEvent"

    PULL_REQUEST_REVIEW = "PullRequestReviewEvent"

    PULL_REQUEST_REVIEW_COMMENT = "PullRequestReviewCommentEvent"

    PUSH = "PushEvent"

    RELEASE = "ReleaseEvent"

    SPONSORSHIP = "SponsorshipEvent"

    WATCH = "WatchEvent"


def __calendar_event_count(event: Event) -> int:
    """Determine if an event would be counted as a calendar event.

    For documentation on the available event types see here:
        https://docs.github.com/en/developers/webhooks-and-events/events/github-event-types#publicevent

    :param event: The event whose calendar activity count need sto be retrieved.s
    :return: The amount of activity for the given event.

    todo: handle screwy timezone stuff
    """
    match event.type:
        case __EventType.FORK:
            return 1
        case __EventType.PUSH:
            # verify that teh event ref matches the commit default repo
            if event.payload["ref"].split("/")[-1] == event.repo.default_branch:
                return len(event.payload["commits"])
        case __EventType.ISSUE:
            if event.payload["action"] == "opened":
                return 1
        case __EventType.PULL_REQUEST:
            if event.payload["action"] == "opened":
                return 1
        case __EventType.PULL_REQUEST_REVIEW:
            if event.payload["action"] == "created":
                return 1

    return 0


def get_max_events_per_day(github: Github, login: str) -> (date, int):
    """Retrieve the maximum amount of events on a single day from the last 90 days.

    The github events api limits the event timeline to 90 days: "Only events created within the past 90 days will be
    included in timelines. Events older than 90 days will not be included (even if the total number of events in the
    timeline is less than 300)." Due to this we ae onl able to return a sample of the most recent activity.

    DO NOT assume that this method will be completely representative of the entire timeline without good reason.

    For documentation on what gets counted as a contribution see here:
        https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-github-profile/managing-contribution-graphs-on-your-profile/viewing-contributions-on-your-profile#what-counts-as-a-contribution

    :param github: The github api client to use when accessing data from github.
    :param login: The login name for the user whose events to pull.
    :return: The day with the most calendar activity and the amount of activity.
    """

    events = github.get_user(login).get_events()

    freq = defaultdict(lambda: 0)

    for event in events:
        if event.created_at.year == 2021 and event.created_at.month == 12 and event.created_at.day == 2:
            freq[event.created_at.date()] += __calendar_event_count(event)

    return max(freq.items(), key=lambda x: x[1])


def get_commits_pre_data_level(max_per_day: int, dilute: bool = True) -> (int, int, int, int, int):
    """Retrieve the amount of commits which must be performed to force a value of `max_per_day` into the lowest level.

    Note that it is generally safe to assume that the lowest data level (data level 0) will be 0; however, this is not
    guaranteed. Take care when setting `dilute` to True since it will generate many more commits.

    :param max_per_day: The greatest amount of activity on any single day.
    :param dilute: If False, the returned boundaries will not be far greater than the amount of current activity, if
    True `get_commits_pre_data_level` will attempt to force the value of `max_per_day` into the lowest possible data
    level.
    :return: A tuple containing the upper bounds for the amount of commit which must be made to put a date into a
    specific data level.
    """
    step = max_per_day if dilute else max_per_day // 4
    start = max_per_day if dilute else 0

    return tuple(range(start, start + step * 4, step))
