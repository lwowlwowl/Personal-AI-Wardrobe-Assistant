from AIwardrobe.utils.config_handler import prompts_conf
from AIwardrobe.utils.path_tool import get_abs_path
from AIwardrobe.utils.logger_handler import logger


def load_system_prompts(lang: str = "zh"):
    key = "main_prompt_path_zh" if lang == "zh" else "main_prompt_path_en"
    try:
        system_prompt_path = get_abs_path(prompts_conf[key])
    except KeyError as e:
        logger.error("[load_system_prompts] prompts config missing main_prompt_path_zh / main_prompt_path_en")
        raise e

    try:
        return open(system_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[load_system_prompts] failed to read system prompt: {e}")
        raise e


def load_report_prompts() -> str:
    try:
        rel = prompts_conf["report_prompt_path"]
    except KeyError as e:
        logger.error("[load_report_prompts] prompts config missing report_prompt_path")
        raise e
    path = get_abs_path(rel)
    try:
        return open(path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[load_report_prompts] failed to read report prompt: {e}")
        raise e


def load_rag_prompts():
    try:
        rag_prompt_path = get_abs_path(prompts_conf["rag_summarize_prompt_path"])
    except KeyError as e:
        logger.error("[load_rag_prompts] prompts config missing rag_summarize_prompt_path")
        raise e

    try:
        return open(rag_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[load_rag_prompts] failed to read RAG prompt: {e}")
        raise e


def load_classify_prompts():
    try:
        classify_prompt_rel_path = prompts_conf["classify_prompt_path"]
    except KeyError as e:
        logger.warning("[load_classify_prompts] classify_prompt_path not set in prompts config")
        raise e

    classify_prompt_path = get_abs_path(classify_prompt_rel_path)
    try:
        return open(classify_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.warning(f"[load_classify_prompts] failed to read classification prompt: {e}")
        raise e


if __name__ == '__main__':
    print(load_system_prompts())
