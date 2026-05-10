# tests/test_main.py

import unittest
from unittest.mock import patch, MagicMock
import sys


class TestMain(unittest.TestCase):

    @patch('app.config.load_settings')
    @patch('app.logs.nexus_logger.build_logger')
    @patch('app.voice.listener.VoiceListener.listen_once', return_value='comando de teste')
    @patch('app.core.command_router.CommandRouter.route')
    @patch('app.voice.speaker.VoiceSpeaker.speak')
    def test_voice_demo(self, mock_speak, mock_route, mock_listen_once, mock_build_logger, mock_load_settings):
        mock_command = MagicMock()
        mock_command.intent = 'sair'
        mock_command.label = 'teste'
        mock_command.args = []
        mock_route.return_value = mock_command
        
        test_args = ['main.py', '--voice-demo']
        with patch.object(sys, 'argv', test_args):
            import main  # Importando aqui para garantir que sys.argv seja atualizado corretamente
            main.main()  # Chamando explicitamente main()
        
        mock_route.assert_called_once_with('comando de teste')
        mock_speak.assert_called_once_with('NEXUS online. Modo demo de voz.')


if __name__ == '__main__':
    unittest.main()
