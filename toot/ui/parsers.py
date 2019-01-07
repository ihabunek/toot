from toot.utils import format_content


def parse_status(status):
    _status = status.get('reblog') or status
    account = parse_account(_status['account'])
    content = list(format_content(_status['content']))
    spoiler_text = list(format_content(_status['spoiler_text'])) if _status['spoiler_text'] else []

    created_at = status['created_at'][:19].split('T')
    boosted_by = parse_account(status['account']) if status['reblog'] else None

    return {
        'account': account,
        'boosted_by': boosted_by,
        'created_at': created_at,
        'content': content,
        'favourited': status.get('favourited'),
        'favourites_count': _status['favourites_count'],
        'id': status['id'],
        'in_reply_to_id': _status.get('in_reply_to_id'),
        'media_attachments': _status['media_attachments'],
        'url': _status['url'],
        'reblogged': status.get('reblogged'),
        'reblogs_count': _status['reblogs_count'],
        'replies_count': _status.get('replies_count', 0),
        'spoiler_text': spoiler_text,
        'sensitive': _status['sensitive'],
        'show_sensitive': False,
    }


def parse_account(account):
    return {
        'id': account['id'],
        'acct': account['acct'],
        'display_name': account['display_name'],
    }
