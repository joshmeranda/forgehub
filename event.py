import time

from github import Event, Github


def __is_calendar_event(event: Event) -> bool:
    """Determine if an event would be counted as a calendar event.

    For documentation on the available event types see here:
        https://docs.github.com/en/developers/webhooks-and-events/events/github-event-types#publicevent

    todo: needs to be implemented
    """
    # Committing to a repository's default branch or gh-pages branch
    # Opening an issue
    # Opening a discussion
    # Answering a discussion
    # Proposing a pull request
    # Submitting a pull request review
    return True


def get_calendar_event_count_after(github: Github, after=None) -> int:
    """Retrieve the amount of events which would be represented on the github activity calendar.

    For documentation on what gets counted as a contribution see here:
        https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-github-profile/managing-contribution-graphs-on-your-profile/viewing-contributions-on-your-profile#what-counts-as-a-contribution
    """
    has_more = True
    counter = 0

    while has_more:
        events = github.get_user("joshmeranda").get_events()

        if events.totalCount < github.per_page:
            has_more = False

        for event in events:
            if after is not None and event.created_at <= after:
                return counter

            if __is_calendar_event(event):
                counter += 1

    return counter
