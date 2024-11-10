from setuptools import find_packages, setup

setup(
    name="bookmanager",
    version="1.0.0",
    packages=find_packages(), # パッケージ化対象を自動設定
    include_package_data=True, # MANIFEST.inを読み込む
    zip_safe=False, # テンプレートファイルのために圧縮しない
    install_requires=[
        # 依存パッケージ
        "flask",
        "requests"
    ]
)