{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.replitPackages.prybar-python311
    pkgs.replitPackages.stderred
    pkgs.postgresql
    pkgs.cairo
    pkgs.ffmpeg-full
    pkgs.freetype
    pkgs.ghostscript
    pkgs.glibcLocales
    pkgs.gobject-introspection
    pkgs.gtk3
    pkgs.lcms2
    pkgs.libGL
    pkgs.libGLU
    pkgs.libimagequant
    pkgs.libjpeg
    pkgs.libtiff
    pkgs.libwebp
    pkgs.libxcrypt
    pkgs.openjpeg
    pkgs.pkg-config
    pkgs.qhull
    pkgs.tcl
    pkgs.tk
    pkgs.xsimd
    pkgs.zlib
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.cairo
      pkgs.freetype
      pkgs.ghostscript
      pkgs.libimagequant
      pkgs.libjpeg
      pkgs.libtiff
      pkgs.libwebp
      pkgs.openjpeg
      pkgs.zlib
    ];
    PYTHONHOME = "${pkgs.python311Full}";
    PYTHONBIN = "${pkgs.python311Full}/bin/python3.11";
    LANG = "en_US.UTF-8";
    STDERREDPATH = "${pkgs.replitPackages.stderred}/bin/stderred";
    PRYBAR_PYTHON_BIN = "${pkgs.replitPackages.prybar-python311}/bin/prybar-python311";
  };
}