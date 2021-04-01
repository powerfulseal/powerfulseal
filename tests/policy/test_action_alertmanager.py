import pytest
from mock import MagicMock, patch

from tests.fixtures import action_alertmanager, ActionUnmuteAlertManager, ActionAlertManager

# single target cases
def test_happy_path(action_alertmanager):
    mock_resp = 'silence_id'
    action_alertmanager.mute = MagicMock(
        return_value=mock_resp
    )
    action_alertmanager.execute()

    # muting should store silence id
    assert(action_alertmanager.silences == {
        'http://example.com': 'silence_id'
    })
    assert(action_alertmanager.proxies == dict(http='http',https='https'))
    # test default silence duration
    action_alertmanager.mute.assert_called_once_with('http://example.com', 900)

    # muting should push unmuting action for cleaning up
    cleanup_action = action_alertmanager.cleanup_actions[0]
    assert(type(cleanup_action) is ActionUnmuteAlertManager)
    assert(cleanup_action.silence_id == 'silence_id')
    assert(cleanup_action.alertmanager_url == 'http://example.com')
    assert(cleanup_action.proxies == dict(http='http',https='https'))

def test_no_proxy(action_alertmanager):
    action_alertmanager.proxies = {}
    action_alertmanager.mute = MagicMock()
    action_alertmanager.execute()
    assert(action_alertmanager.cleanup_actions[0].proxies == {})

# autoUnmute is set to false
def test_autounmute_disabled(action_alertmanager):
    action_alertmanager.schema["actions"][0]["mute"] = {'autoUnmute': False}
    action_alertmanager.mute = MagicMock()
    action_alertmanager.execute()
    # no clean up action when autoUnmute is false
    assert(len(action_alertmanager.cleanup_actions) == 0)

# what if 'mute' is None
def test_mute_is_none(action_alertmanager):
    action_alertmanager.schema["actions"][0]["mute"] = None
    action_alertmanager.mute = MagicMock()
    action_alertmanager.execute()
    # test default silence duration
    action_alertmanager.mute.assert_called_once_with('http://example.com', 900)

def test_duration_override(action_alertmanager):
    action_alertmanager.schema["actions"][0]["mute"] = {'duration': 123}
    action_alertmanager.mute = MagicMock()
    action_alertmanager.execute()
    # test default silence duration
    action_alertmanager.mute.assert_called_once_with('http://example.com', 123)

# multiple targets cases
@patch.object(ActionAlertManager, 'mute')
def test_multiple_targets_happy_path(mute):
    mute.side_effect = ['silence_1', 'silence_2']
    logger = MagicMock()
    action_alertmanager = ActionAlertManager(
        name="test alert manager action",
        schema=dict(
            targets = [
                dict(url="http://example1.com"),
                dict(url="http://example2.com")
            ],
            actions= [
                dict(mute = dict())
            ],
            proxies=dict(http='http',https='https')
        ),
        logger=logger,
    )
    action_alertmanager.execute()
    assert(action_alertmanager.silences == {
        'http://example1.com': 'silence_1',
        'http://example2.com': 'silence_2'
    })
    cleanup_action = action_alertmanager.cleanup_actions
    assert(len(cleanup_action) == 2)
