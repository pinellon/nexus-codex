# tests/test_main.py

import unittest
from unittest.mock import patch, MagicMock
import sys


class TestMain(unittest.TestCase):

    @patch('app.config.load_settings', return_value=MagicMock())
    @patch('app.logs.nexus_logger.build_logger')
    @patch('app.voice.listener.VoiceListener.listen_once', return_value='comando de teste')
    @patch('app.core.command_router.CommandRouter.route')
    @patch('app.voice.speaker.VoiceSpeaker.speak')
    def test_voice_demo(self, mock_speak, mock_route, mock_listen_once, mock_build_logger, mock_load_settings):
        # Setup do mock para garantir que a lógica funcione isoladamente
        mock_command = MagicMock()
        mock_command.intent = 'sair'
        mock_command.label = 'teste'
        mock_command.args = []
        mock_route.return_value = mock_command
        
        # Argumentos para simular execução
        test_args = ['main.py', '--voice-demo']
        with patch.object(sys, 'argv', test_args):
            import main  # Importação dentro do contexto de patch
            main.main()  # Execução do método principal
        
        # Verificação das chamadas de função e interações
        mock_route.assert_called_once_with('comando de teste')
        mock_speak.assert_called_once_with('NEXUS online. Modo demo de voz.')


if __name__ == '__main__':
    unittest.main()
