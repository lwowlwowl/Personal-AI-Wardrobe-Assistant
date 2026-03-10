from AIwardrobe.utils.config_handler import prompts_conf
from AIwardrobe.utils.path_tool import get_abs_path
from AIwardrobe.utils.logger_handler import logger


def load_system_prompts(lang: str = "zh"):
    key = "main_prompt_path_zh" if lang == "zh" else "main_prompt_path_en"
    try:
        system_prompt_path = get_abs_path(prompts_conf[key])
    except KeyError as e:
        logger.error(f"[load_system_prompts]在yaml配置项中没有main_prompt_path配置项")
        raise e

    try:
        return open(system_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[load_system_prompts]解析系统提示词出错，{str(e)}")
        raise e


def load_rag_prompts():
    try:
        rag_prompt_path = get_abs_path(prompts_conf["rag_summarize_prompt_path"])
    except KeyError as e:
        logger.error(f"[load_rag_prompts]在yaml配置项中没有rag_summarize_prompt_path配置项")
        raise e

    try:
        return open(rag_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[load_rag_prompts]解析RAG提示词出错，{str(e)}")
        raise e


def load_classify_prompts():
    try:
        classify_prompt_rel_path = prompts_conf["classify_prompt_path"]
    except KeyError as e:
        logger.warning("[load_classify_prompts]未配置classify_prompt_path")
        raise e

    classify_prompt_path = get_abs_path(classify_prompt_rel_path)
    try:
        return open(classify_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.warning(f"[load_classify_prompts]读取报告提示词失败")
        raise e


if __name__ == '__main__':
    print(load_system_prompts())
