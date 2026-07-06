# class Palette:
#     SURFACE_LOWEST    = "#0e0e0e"
#     SURFACE           = "#111111"
#     SURFACE_LOW       = "#181818"
#     SURFACE_CONTAINER = "#1e1e1e"
#     SURFACE_HIGH      = "#252525"
#     SURFACE_HIGHEST   = "#303030"

#     PRIMARY           = "#f2ca50"
#     PRIMARY_DIM       = "#d4af37"
#     PRIMARY_FIXED_DIM = "#e9c349"
#     ON_PRIMARY        = "#1a1500"

#     ON_SURFACE        = "#e4e4e4"
#     ON_SURFACE_VAR    = "#888888"
#     OUTLINE           = "#2e2e2e"
#     OUTLINE_BRIGHT    = "#484040"
#     OUTLINE_VAR = "#e4e4e4"

#     ERROR             = "#e05252"
#     WARNING           = "#d4af37"
#     SUCCESS           = "#4caf7d"
#     INFO              = "#5b8dee"
#     BENIGN            = "#5a5a5a"

#     NAV_W             = 220
#     TOPBAR_H          = 52
#     RIGHT_PANEL_W     = 280


#   # Spacing (px)
#     RADIUS  = 12
#     PAD_XL = 28
#     PAD_LG = 18
#     PAD_MD = 12
#     PAD_SM = 7
#     PAD_XS = 4

#     WIN_MIN_W = 1100
#     WIN_MIN_H = 680

#     _FONT = ("Helvetica Neue", "Segoe UI", "SF Pro Display", "Arial")

#     DISPLAY  = 30
#     TITLE_LG = 15
#     TITLE_MD = 13
#     BODY     = 12
#     LABEL    = 10
#     MICRO    = 9
    
#     DISPLAY_LG  = 36
#     HEADLINE_SM = 18
#     BODY_MD     = 12
#     LABEL_SM    = 10

#     @classmethod
#     def font(cls, size=None, weight="normal"):
#         return (cls._FONT[0], size or cls.BODY, weight)

#     @classmethod
#     def bold(cls, size=None):
#         return cls.font(size, "bold")


# WHITE

# class Palette:
#     SURFACE_LOWEST    = "#f0f0f0"
#     SURFACE           = "#ffffff"
#     SURFACE_LOW       = "#f7f7f7"
#     SURFACE_CONTAINER = "#f0f0f0"
#     SURFACE_HIGH      = "#e8e8e8"
#     SURFACE_HIGHEST   = "#dedede"

#     PRIMARY           = "#b8860b"
#     PRIMARY_DIM       = "#a0740a"
#     PRIMARY_FIXED_DIM = "#c49510"
#     ON_PRIMARY        = "#ffffff"

#     ON_SURFACE        = "#1a1a1a"
#     ON_SURFACE_VAR    = "#555555"
#     OUTLINE           = "#d0d0d0"
#     OUTLINE_BRIGHT    = "#b0b0b0"
#     OUTLINE_VAR       = "#1a1a1a"

#     ERROR             = "#c0392b"
#     WARNING           = "#a0740a"
#     SUCCESS           = "#2e7d52"
#     INFO              = "#2563c7"
#     BENIGN            = "#909090"

#     NAV_W             = 220
#     TOPBAR_H          = 52
#     RIGHT_PANEL_W     = 280

#     # Spacing (px)
#     RADIUS  = 12
#     PAD_XL = 28
#     PAD_LG = 18
#     PAD_MD = 12
#     PAD_SM = 7
#     PAD_XS = 4

#     WIN_MIN_W = 1100
#     WIN_MIN_H = 680

#     _FONT = ("Helvetica Neue", "Segoe UI", "SF Pro Display", "Arial")

#     DISPLAY  = 30
#     TITLE_LG = 15
#     TITLE_MD = 13
#     BODY     = 12
#     LABEL    = 10
#     MICRO    = 9

#     DISPLAY_LG  = 36
#     HEADLINE_SM = 18
#     BODY_MD     = 12
#     LABEL_SM    = 10

#     @classmethod
#     def font(cls, size=None, weight="normal"):
#         return (cls._FONT[0], size or cls.BODY, weight)

#     @classmethod
#     def bold(cls, size=None):
#         return cls.font(size, "bold")


# TEAL

class Palette:
    # Teal Light Theme

    SURFACE_LOWEST    = "#e8f7f6"
    SURFACE           = "#ffffff"
    SURFACE_LOW       = "#f1fbfa"
    SURFACE_CONTAINER = "#dff4f2"
    SURFACE_HIGH      = "#cfeceb"
    SURFACE_HIGHEST   = "#bfe4e2"

    PRIMARY           = "#0f766e"   # teal-700
    PRIMARY_DIM       = "#115e59"   # teal-800
    PRIMARY_FIXED_DIM = "#14b8a6"   # teal-500
    ON_PRIMARY        = "#ffffff"

    ON_SURFACE        = "#0f172a"
    ON_SURFACE_VAR    = "#475569"
    OUTLINE           = "#b6d7d5"
    OUTLINE_BRIGHT    = "#8fc8c3"
    OUTLINE_VAR       = "#134e4a"

    ERROR             = "#dc2626"
    WARNING           = "#d97706"
    SUCCESS           = "#15803d"
    INFO              = "#0284c7"
    BENIGN            = "#94a3b8"

    NAV_W             = 220
    TOPBAR_H          = 52
    RIGHT_PANEL_W     = 280

    # Spacing (px)
    RADIUS  = 12
    PAD_XL = 28
    PAD_LG = 18
    PAD_MD = 12
    PAD_SM = 7
    PAD_XS = 4

    WIN_MIN_W = 1100
    WIN_MIN_H = 680

    _FONT = ("Helvetica Neue", "Segoe UI", "SF Pro Display", "Arial")

    DISPLAY  = 30
    TITLE_LG = 15
    TITLE_MD = 13
    BODY     = 12
    LABEL    = 10
    MICRO    = 9

    DISPLAY_LG  = 36
    HEADLINE_SM = 18
    BODY_MD     = 12
    LABEL_SM    = 10

    @classmethod
    def font(cls, size=None, weight="normal"):
        return (cls._FONT[0], size or cls.BODY, weight)

    @classmethod
    def bold(cls, size=None):
        return cls.font(size, "bold")