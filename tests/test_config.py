import os
import pytest

from toot import User, App, config


@pytest.fixture
def sample_config():
    return {
        'apps': {
            'foo.social': {
                'base_url': 'https://foo.social',
                'client_id': 'abc',
                'client_secret': 'def',
                'instance': 'foo.social'
            },
            'bar.social': {
                'base_url': 'https://bar.social',
                'client_id': 'ghi',
                'client_secret': 'jkl',
                'instance': 'bar.social'
            },
        },
        'users': {
            'foo@bar.social': {
                'access_token': 'mno',
                'instance': 'bar.social',
                'username': 'ihabunek'
            }
        },
        'active_user': 'foo@bar.social',
    }


def test_extract_active_user_app(sample_config):
    user, app = config.extract_user_app(sample_config, sample_config['active_user'])

    assert isinstance(user, User)
    assert user.instance == 'bar.social'
    assert user.username == 'ihabunek'
    assert user.access_token == 'mno'

    assert isinstance(app, App)
    assert app.instance == 'bar.social'
    assert app.base_url == 'https://bar.social'
    assert app.client_id == 'ghi'
    assert app.client_secret == 'jkl'


def test_extract_active_when_no_active_user(sample_config):
    # When there is no active user
    assert config.extract_user_app(sample_config, None) == (None, None)

    # When active user does not exist for whatever reason
    assert config.extract_user_app(sample_config, 'does-not-exist') == (None, None)

    # When active app does not exist for whatever reason
    sample_config['users']['foo@bar.social']['instance'] = 'does-not-exist'
    assert config.extract_user_app(sample_config, 'foo@bar.social') == (None, None)


def test_save_app(sample_config):
    app = App('xxx.yyy', 2, 3, 4)
    app2 = App('moo.foo', 5, 6, 7)

    app_count = len(sample_config['apps'])
    assert 'xxx.yyy' not in sample_config['apps']
    assert 'moo.foo' not in sample_config['apps']

    # Sets
    config.save_app.__wrapped__(sample_config, app)
    assert len(sample_config['apps']) == app_count + 1
    assert 'xxx.yyy' in sample_config['apps']
    assert sample_config['apps']['xxx.yyy']['instance'] == 'xxx.yyy'
    assert sample_config['apps']['xxx.yyy']['base_url'] == 2
    assert sample_config['apps']['xxx.yyy']['client_id'] == 3
    assert sample_config['apps']['xxx.yyy']['client_secret'] == 4

    # Overwrites
    config.save_app.__wrapped__(sample_config, app2)
    assert len(sample_config['apps']) == app_count + 2
    assert 'xxx.yyy' in sample_config['apps']
    assert 'moo.foo' in sample_config['apps']
    assert sample_config['apps']['xxx.yyy']['instance'] == 'xxx.yyy'
    assert sample_config['apps']['xxx.yyy']['base_url'] == 2
    assert sample_config['apps']['xxx.yyy']['client_id'] == 3
    assert sample_config['apps']['xxx.yyy']['client_secret'] == 4
    assert sample_config['apps']['moo.foo']['instance'] == 'moo.foo'
    assert sample_config['apps']['moo.foo']['base_url'] == 5
    assert sample_config['apps']['moo.foo']['client_id'] == 6
    assert sample_config['apps']['moo.foo']['client_secret'] == 7

    # Idempotent
    config.save_app.__wrapped__(sample_config, app2)
    assert len(sample_config['apps']) == app_count + 2
    assert 'xxx.yyy' in sample_config['apps']
    assert 'moo.foo' in sample_config['apps']
    assert sample_config['apps']['xxx.yyy']['instance'] == 'xxx.yyy'
    assert sample_config['apps']['xxx.yyy']['base_url'] == 2
    assert sample_config['apps']['xxx.yyy']['client_id'] == 3
    assert sample_config['apps']['xxx.yyy']['client_secret'] == 4
    assert sample_config['apps']['moo.foo']['instance'] == 'moo.foo'
    assert sample_config['apps']['moo.foo']['base_url'] == 5
    assert sample_config['apps']['moo.foo']['client_id'] == 6
    assert sample_config['apps']['moo.foo']['client_secret'] == 7


def test_delete_app(sample_config):
    app = App('foo.social', 2, 3, 4)

    app_count = len(sample_config['apps'])

    assert 'foo.social' in sample_config['apps']

    config.delete_app.__wrapped__(sample_config, app)
    assert 'foo.social' not in sample_config['apps']
    assert len(sample_config['apps']) == app_count - 1

    # Idempotent
    config.delete_app.__wrapped__(sample_config, app)
    assert 'foo.social' not in sample_config['apps']
    assert len(sample_config['apps']) == app_count - 1


def test_get_config_file_path():
    fn = config.get_config_file_path

    os.unsetenv('XDG_CONFIG_HOME')
    os.environ.pop('XDG_CONFIG_HOME', None)

    assert fn() == os.path.expanduser('~/.config/toot/config.json')

    os.environ['XDG_CONFIG_HOME'] = '/foo/bar/config'

    assert fn() == '/foo/bar/config/toot/config.json'

    os.environ['XDG_CONFIG_HOME'] = '~/foo/config'

    assert fn() == os.path.expanduser('~/foo/config/toot/config.json')
