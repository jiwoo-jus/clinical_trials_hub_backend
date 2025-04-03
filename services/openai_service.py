# /Users/jiwoo/WorkSpace/ClinicalTrialsHub/clinical_trials_hub_web/clinical_trials_hub_backend/services/openai_service.py
import os
import json
from pathlib import Path
from openai import AzureOpenAI  # Assuming AzureOpenAI is installed and configured
import time

def load_prompt(file_name: str, variables: dict) -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / file_name
    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()
    for key, value in variables.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    return template

def refine_query(input_data: dict) -> dict:
    print("openai_service.py - refine_query")
    print("input_data: ", input_data)
    prompt_system = load_prompt("refine_query_prompt_system.md", {})
    # input_data 전체를 JSON 문자열로 변환하여 "inputData" 변수에 넣습니다.
    prompt_user = load_prompt("refine_query_prompt_user.md", {
        "inputData": json.dumps(input_data, ensure_ascii=False, indent=2)
    })
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user}
        ],
        response_format={"type": "json_object"}
    )
    refined_query = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(refined_query)
    except Exception as e:
        raise Exception("Failed to parse Refined Query response") from e
    return parsed


def chat_about_paper(paper_content: str, user_question: str) -> dict:
    prompt = load_prompt("chatAboutPaper.md", {"paperContent": paper_content, "userQuestion": user_question})
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that answers questions about clinical trial study papers."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    result_text = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(result_text)
    except Exception:
        parsed = {"answer": result_text, "evidence": []}
    return parsed

def extract_structured_info(paper_content: str) -> dict:
    print("[openai_service.py - extract_structured_info] start")
    """
    여러 개의 분할된 프롬프트 템플릿을 사용하여 구조화된 데이터를 추출합니다.
    이제 프롬프트는 그룹별(예: protocolSection, resultsSection)로 분리되어 있으며,
    각 그룹에 대해 별도의 키("protocolSection", "resultsSection")로 결과를 감쌉니다.
    
    각 프롬프트는 스트리밍 방식으로 요청하며, JSON 파싱 실패 시 최대 2회 재시도합니다.
    """
    # 그룹별 프롬프트 폴더와 최종 키 매핑
    group_mapping = {
        "ie/1_protocol_section": "protocolSection",
        "ie/2_results_section": "resultsSection"
    }
    
    # 분할된 프롬프트 파일 목록 (각 파일은 그룹별로 위치함)
    prompt_files = [
        "ie/1_protocol_section/1_identification.md",
        "ie/1_protocol_section/2_description_and_conditions.md",
        "ie/1_protocol_section/3_design.md",
        "ie/1_protocol_section/4_arms_interventions.md",
        "ie/1_protocol_section/5_outcomes.md",
        "ie/1_protocol_section/6_eligibility.md",
        "ie/2_results_section/1_baseline_characteristics.md",
    ]
    
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )
    
    # 그룹별 결과를 담을 aggregated_data 딕셔너리 초기화
    aggregated_data = {}
    for folder in group_mapping:
        group_key = group_mapping[folder]
        aggregated_data[group_key] = {}
    
    # 각 프롬프트 파일 처리
    for prompt_file in prompt_files:
        group = None
        for folder in group_mapping:
            if prompt_file.startswith(folder):
                group = group_mapping[folder]
                break
        if group is None:
            # 매칭되는 그룹이 없으면 건너뜁니다.
            continue

        prompt = load_prompt(prompt_file, {"pmc_text": paper_content})
        retries = 0
        success = False
        while retries < 3 and not success:
            collected_messages = []
            metadata = {}
            last_chunk = None
            call_start = time.time()
            print(f'call_start: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(call_start))}')
            try:
                # 스트리밍 응답 요청
                response_stream = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an expert assistant trained to extract structured data in JSON format from clinical trial articles."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    stream=True,
                    stream_options={"include_usage": True}
                )
                for chunk in response_stream:
                    last_chunk = chunk
                    if not chunk.choices:
                        print("\n******** no chunk.choices ********\n")
                        continue
                    chunk_message = chunk.choices[0].delta.content
                    # print(chunk_message, end='', flush=True)
                    collected_messages.append(chunk_message)
            except Exception as e:
                call_end = time.time()
                print(f'call_end: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(call_end))}')
                print("duration: ", time.strftime("%M:%S", time.gmtime(call_end - call_start)))
                print(f"\n***** Unexpected Error *******\nMessage: {str(e)}")
                metadata = {
                    "Error Message": str(e),
                    "call_start": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(call_start)),
                    "call_end": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(call_end)),
                    "duration": time.strftime("%M:%S", time.gmtime(call_end - call_start))
                }
                content = ''.join(msg for msg in collected_messages if msg is not None) if collected_messages else ''
                return metadata, content
            call_end = time.time()
            print("call_end: ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(call_end)))
            print("duration: ", time.strftime("%M:%S", time.gmtime(call_end - call_start)))
            metadata = {
                "model": last_chunk.model,
                "prompt_file_path": prompt_file,
                "prompt_tokens": last_chunk.usage.prompt_tokens,
                "completion_tokens": last_chunk.usage.completion_tokens,
                "total_tokens": last_chunk.usage.total_tokens,
                "call_start": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(call_start)),
                "call_end": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(call_end)),
                "duration": time.strftime("%M:%S", time.gmtime(call_end - call_start)),
                "id": last_chunk.id,
                "created": last_chunk.created,
            }
            content = ''.join(msg for msg in collected_messages if msg is not None) if collected_messages else ''
            try:
                # JSON 파싱 시도
                partial_data = json.loads(content)
                # 그룹별 결과에 병합 (키 충돌 시 후속 값이 덮어씌워집니다)
                aggregated_data[group].update(partial_data)
                success = True
                print(f"[extract_structured_info] Success: {prompt_file}")
            except Exception as e:
                    retries += 1
                    if retries >= 3:
                        aggregated_data[group][f"error_{prompt_file}"] = f"Failed after retries: {str(e)}"
                        print(f"[extract_structured_info] Fail: {prompt_file}")
    
    return aggregated_data


# --- 캐시 관련 코드 추가 ---

def get_cache_filepath(pmc_id: str) -> Path:
    cache_dir = Path(__file__).parent.parent / "cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / f"{pmc_id}.json"

def get_structured_info_with_cache(pmc_id: str, paper_content: str) -> dict:
    """
    주어진 pmc_id에 대해 캐시된 구조화 정보가 있으면 반환하고,
    없으면 extract_structured_info()를 호출하여 결과를 저장한 후 반환합니다.
    """
    cache_file = get_cache_filepath(pmc_id)
    if cache_file.exists():
        print(f"Found cached data {cache_file}. Loading...")
        with open(cache_file, "r", encoding="utf-8") as f:
            cached = json.load(f)
            return cached
    else:
        print(f"No cached data found for {pmc_id}. Generating new data...")
        result = extract_structured_info(paper_content)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Saved structured info to cache: {cache_file}")
        return result