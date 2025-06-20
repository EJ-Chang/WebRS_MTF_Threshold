{ pkgs }: {
  deps = [
	# Python 3.13 核心
	pkgs.python313Full
	pkgs.python313Packages.pip
	pkgs.python313Packages.setuptools
	pkgs.python313Packages.wheel

	# 數據科學核心套件
	pkgs.python313Packages.numpy
	pkgs.python313Packages.pandas
	pkgs.python313Packages.scipy
	pkgs.python313Packages.matplotlib
	pkgs.python313Packages.plotly

	# Web 框架
	pkgs.python313Packages.streamlit

	# 圖像處理
	pkgs.python313Packages.pillow
	pkgs.python313Packages.opencv4

	# 資料庫
	pkgs.python313Packages.sqlalchemy

	# 系統工具
	pkgs.python313Packages.psutil
	pkgs.python313Packages.requests

	# 系統依賴（編譯套件需要）
	pkgs.gcc
	pkgs.pkg-config
	pkgs.libffi
	pkgs.openssl
	pkgs.zlib
	pkgs.freetype
	pkgs.fontconfig
	pkgs.glib
	pkgs.cairo
	pkgs.pango
	pkgs.gdk-pixbuf
	pkgs.atk
	pkgs.gtk3

	# OpenCV 相關依賴
	pkgs.ffmpeg
	pkgs.libv4l

	# 字體支援
	pkgs.dejavu_fonts
	pkgs.liberation_ttf
  ];

  env = {
	# 設定 Python 路徑
	PYTHONPATH = "";
	PYTHONHOME = "";

	# 設定 pip 快取
	PIP_CACHE_DIR = "/tmp/pip-cache";

	# 設定字體路徑（對 matplotlib 有用）
	FONTCONFIG_PATH = "${pkgs.fontconfig.out}/etc/fonts";

	# OpenCV 設定
	OPENCV_LOG_LEVEL = "ERROR";

	# 確保使用正確的 Python
	PYTHON = "${pkgs.python313Full}/bin/python";
  };
}