
import unittest
from unittest.mock import Mock, patch
from main import agentspace_settings_checker

class TestAgentspaceSettingsChecker(unittest.TestCase):

    def test_agentspace_settings_checker_no_id(self):
        req = Mock(get_json=Mock(return_value={}), args={})
        result, code = agentspace_settings_checker(req)
        self.assertEqual(code, 400)
        self.assertEqual(result, 'No agentspace_id provided.')

    @patch('main.aiplatform')
    def test_agentspace_settings_checker_with_id_json_enabled(self, mock_aiplatform):
        mock_agent = Mock()
        mock_agent.model_armor_enabled = True
        mock_aiplatform.Agent.get.return_value = mock_agent

        req = Mock(get_json=Mock(return_value={'agentspace_id': '123'}), args={})
        result = agentspace_settings_checker(req)
        self.assertEqual(result, {
            'agentspace_id': '123',
            'model_armor_enabled': True
        })

    @patch('main.aiplatform')
    def test_agentspace_settings_checker_with_id_args_disabled(self, mock_aiplatform):
        mock_agent = Mock()
        mock_agent.model_armor_enabled = False
        mock_aiplatform.Agent.get.return_value = mock_agent

        req = Mock(get_json=Mock(return_value={}), args={'agentspace_id': '456'})
        result = agentspace_settings_checker(req)
        self.assertEqual(result, {
            'agentspace_id': '456',
            'model_armor_enabled': False
        })

    @patch('main.aiplatform')
    def test_agentspace_settings_checker_exception(self, mock_aiplatform):
        mock_aiplatform.Agent.get.side_effect = Exception('Test exception')

        req = Mock(get_json=Mock(return_value={'agentspace_id': '789'}), args={})
        result, code = agentspace_settings_checker(req)
        self.assertEqual(code, 500)
        self.assertEqual(result, 'Test exception')

if __name__ == '__main__':
    unittest.main()
