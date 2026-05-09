# tests/test_main.py

import unittest
from unittest.mock import patch, MagicMock
import sys

class TestMain(unittest.TestCase):

    @patch('app.config.load_settings')
    @patch('app.logs.nexus_logger.build_logger')
    @patch('app.voice.listener.VoiceListener.listen_once', return_value='comando de teste')
    @patch('app.core.command_router.CommandRouter.route')
    def test_voice_demo(self, mock_route, mock_listen_once, mock_build_logger, mock_load_settings):
        mock_command = MagicMock()
        mock_command.intent = 'sair'
        mock_command.label = 'teste'
        mock_command.args = []
        mock_route.return_value = mock_command
        
        test_args = ['main.py', '--voice-demo']
        with patch.object(sys, 'argv', test_args):
            from main import main
            main()
        
        mock_route.assert_called_once_with('comando de teste')

if __name__ == '__main__':
    unittest.main()