from styles import ColorScheme, Typography
from layout import LayoutManager

class ThemeManager:
    def __init__(self, color_scheme: ColorScheme, typography: Typography, layout_manager: LayoutManager):
        self.color_scheme = color_scheme
        self.typography = typography
        self.layout_manager = layout_manager

    def apply_theme(self, ui_component):
        self.layout_manager.apply_layout(ui_component)
        self.color_scheme.apply_colors(ui_component)
        self.typography.apply_typography(ui_component)

    def reset_theme(self, ui_component):
        self.layout_manager.reset_layout(ui_component)
        self.color_scheme.reset_colors(ui_component)
        self.typography.reset_typography(ui_component)

# Resto do conteúdo que antes estava aqui deve ser distribuído entre os novos módulos `styles` e `layout` 