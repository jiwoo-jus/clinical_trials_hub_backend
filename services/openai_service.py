import os
import json
import asyncio
from pathlib import Path
# Use AsyncAzureOpenAI for asynchronous operations
from openai import AzureOpenAI 
from openai import AsyncAzureOpenAI
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

# Pass the AsyncAzureOpenAI client instance
async def process_prompt_file(prompt_file: str, paper_content: str, client: AsyncAzureOpenAI) -> dict:
    """
    단일 프롬프트 파일에 대해 비동기 스트리밍 응답을 처리합니다.
    최대 3회 재시도하며, 성공 시 JSON 파싱된 결과를 반환합니다.
    """
    prompt = load_prompt(prompt_file, {"pmc_text": paper_content})
    retries = 0
    success = False
    last_chunk = None
    while retries < 3 and not success:
        collected_messages = []
        try:
            call_start = time.time()
            print(f'call_start: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(call_start))}')
            # Use .create instead of .acreate
            response_stream = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert assistant trained to extract structured data in JSON format from clinical trial articles."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                stream=True,
                stream_options={"include_usage": True}
            )
            async for chunk in response_stream:
                last_chunk = chunk
                # Check if delta and content exist before accessing
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    chunk_message = chunk.choices[0].delta.content
                    collected_messages.append(chunk_message)
                # Handle potential usage information if needed (often comes at the end)
                # elif chunk.usage:
                #     print(f"Usage: {chunk.usage}")

            call_end = time.time()
            print("call_end:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(call_end)))
            print("duration:", time.strftime("%M:%S", time.gmtime(call_end - call_start)))

            # Ensure collected_messages is not empty before joining and parsing
            if not collected_messages:
                 # Handle cases where no content was received, possibly log or retry differently
                 print(f"[extract_structured_info] Warning: No content received for {prompt_file}. Last chunk: {last_chunk}")
                 retries += 1
                 await asyncio.sleep(1) # Optional: wait before retrying
                 continue # Go to next retry attempt

            content = ''.join(collected_messages)
            # JSON 파싱 시도
            partial_data = json.loads(content)
            success = True
            print(f"[extract_structured_info] Success: {prompt_file}")
            return partial_data
        except json.JSONDecodeError as e:
            retries += 1
            print(f"[extract_structured_info] JSON Decode Error on attempt {retries} for {prompt_file}: {e}")
            print(f"Received content: {content}") # Log the problematic content
            if retries >= 3:
                print(f"[extract_structured_info] Fail (JSON Decode): {prompt_file}")
                return {f"error_{prompt_file}": f"Failed after retries (JSON Decode): {str(e)} - Content: {content}"}
            await asyncio.sleep(1) # Wait before retrying
        except Exception as e:
            retries += 1
            print(f"[extract_structured_info] Error on attempt {retries} for {prompt_file}: {type(e).__name__} - {e}")
            if retries >= 3:
                print(f"[extract_structured_info] Fail: {prompt_file}")
                # Provide more specific error if possible
                error_message = f"Failed after retries: {type(e).__name__} - {str(e)}"
                return {f"error_{prompt_file}": error_message}
            await asyncio.sleep(1) # Wait before retrying

async def extract_structured_info(paper_content: str) -> dict:
    """
    여러 분할된 프롬프트를 비동기적으로 호출하여 구조화된 데이터를 추출합니다.
    그룹별(예: protocolSection, resultsSection)로 결과를 병합합니다.
    """
    start_time = time.time()
    print(f"[openai_service.py - extract_structured_info] start at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
    # 그룹별 프롬프트 폴더와 최종 키 매핑
    group_mapping = {
        "ie/1_protocol_section": "protocolSection",
        "ie/2_results_section": "resultsSection"
    }

    prompt_files = [
        "ie/1_protocol_section/1_identification.md",
        "ie/1_protocol_section/2_description_and_conditions.md",
        "ie/1_protocol_section/3_design.md",
        "ie/1_protocol_section/4_arms_interventions.md",
        "ie/1_protocol_section/5_outcomes.md",
        "ie/1_protocol_section/6_eligibility.md",
        "ie/2_results_section/1_baseline_characteristics.md",
    ]

    # Use AsyncAzureOpenAI
    client = AsyncAzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )

    # 그룹별 결과를 담을 aggregated_data 초기화
    aggregated_data = {}
    for folder in group_mapping:
        group_key = group_mapping[folder]
        aggregated_data[group_key] = {}

    tasks = []
    # 각 프롬프트 파일에 대해 비동기 작업(task)을 생성
    for prompt_file in prompt_files:
        group = None
        for folder in group_mapping:
            if prompt_file.startswith(folder):
                group = group_mapping[folder]
                break
        if group is None:
            print(f"Warning: Prompt file '{prompt_file}' does not belong to any defined group. Skipping.")
            continue
        # Pass the client instance to the processing function
        task = asyncio.create_task(process_prompt_file(prompt_file, paper_content, client))
        tasks.append((group, prompt_file, task))

    # 모든 작업을 기다린 후 결과를 그룹별로 병합
    results = await asyncio.gather(*(task for _, _, task in tasks))

    for i, (group, prompt_file, _) in enumerate(tasks):
        result = results[i]
        # Check if the result contains an error key before updating
        is_error = any(key.startswith("error_") for key in result.keys())
        if is_error:
            print(f"Error processing {prompt_file}: {result}")
            # Decide how to handle errors: merge them or skip them
            # Merging errors for visibility:
            aggregated_data[group].update(result)
        else:
            aggregated_data[group].update(result)

    end_time = time.time()
    duration = end_time - start_time
    print(f"[openai_service.py - extract_structured_info] end at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    print(f"[openai_service.py - extract_structured_info] duration: {time.strftime('%M:%S', time.gmtime(duration))}")

    return aggregated_data

def get_cache_filepath(pmc_id: str) -> Path:
    cache_dir = Path(__file__).parent.parent / "cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / f"{pmc_id}.json"

async def get_structured_info_with_cache(pmc_id: str, paper_content: str) -> dict:
    """
    주어진 pmc_id에 대해 캐시된 구조화 정보가 있으면 반환하고,
    없으면 extract_structured_info()를 호출하여 결과를 캐시한 후 반환합니다.
    """
    cache_file = get_cache_filepath(pmc_id)
    if cache_file.exists():
        print(f"Found cached data {cache_file}. Loading...")
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            return cached
        except json.JSONDecodeError as e:
             print(f"Error loading cached data from {cache_file}: {e}. Regenerating...")
             # Optionally remove or rename the corrupted cache file
             # os.remove(cache_file)

    print(f"No valid cached data found for {pmc_id}. Generating new data...")
    result = await extract_structured_info(paper_content)
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Saved structured info to cache: {cache_file}")
    except Exception as e:
        print(f"Error saving data to cache file {cache_file}: {e}")
    return result
