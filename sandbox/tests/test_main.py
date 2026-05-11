# tests/test_main.py

import unittest
from unittest.mock import patch, MagicMock
import sys


class TestMain(unittest.TestCase):

    @patch('app.config.load_settings', return_value=MagicMock())
    @patch('app.logs.nexus_logger.build_logger')
    @patch('app.voice.listener.VoiceListener.listen_once', side_effect=["comando de teste", "sair"])
    @patch('app.core.command_router.CommandRouter.route')
    @patch('app.voice.speaker.VoiceSpeaker.speak')
    def test_voice_demo(self, mock_speak, mock_route, mock_listen_once, mock_build_logger, mock_load_settings):
        # Configuração do mock para garantir que a lógica seja independente
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
        mock_route.assert_any_call('comando de teste')
        mock_speak.assert_called_once_with('NEXUS online. Modo demo de voz.')

if __name__ == '__main__':
    unittest.main()
