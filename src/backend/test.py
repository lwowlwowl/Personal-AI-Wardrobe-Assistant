try:
    from fastapi import FastAPI

    print("✅ FastAPI 导入成功!")
    print(f"FastAPI 版本: {FastAPI.__module__}")
except ImportError as e:
    print(f"❌ 导入失败: {e}")

    # 检查包是否安装
    import pkg_resources

    installed_packages = [d.project_name for d in pkg_resources.working_set]
    if 'fastapi' in installed_packages:
        print("FastAPI 已安装，但导入有问题")
    else:
        print("FastAPI 未安装")