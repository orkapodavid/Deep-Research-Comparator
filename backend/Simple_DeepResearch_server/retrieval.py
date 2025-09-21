import base64
import json
import os

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../../.env")
load_dotenv()

CLUEWEB_API_KEY = os.getenv("CLUEWEB_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")


def query_serper(query, num_docs=10):
    """
    Search using Serper API as fallback when ClueWeb is not available
    """
    if not SERPER_API_KEY:
        print("No Serper API key found")
        return [], []

    url = "https://google.serper.dev/search"
    payload = {"q": query, "num": min(num_docs, 10)}  # Serper has a limit
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            documents = []
            urls = []

            # Extract organic results
            organic = data.get("organic", [])
            for result in organic[:num_docs]:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                link = result.get("link", "")

                # Combine title and snippet as document text
                doc_text = f"Title: {title}\n\nContent: {snippet}"
                documents.append(doc_text)
                urls.append(link)

            return documents, urls
        else:
            print(f"Serper API request failed with status code: {response.status_code}")
            return [], []
    except Exception as e:
        print(f"Error with Serper search: {e}")
        return [], []


def query_clueweb(
    query,
    num_docs=10,
    num_top_docs_to_read=1,
    num_outlinks_per_doc=None,
    with_id=False,
    with_url=False,
    num_tries=3,
):
    """
    Args:
        - query, the query to search
        - num_docs, the number of documents to return
        - num_outlinks_per_doc is the maximum number of outlinks to
            return per document if the outlinked document is in clueweb22
    Returns:
        - returned_cleaned_text: a dictionary, keys is the cluewebid, values is a tuple of (cleaned text, url)
        - returned_outlinks: a dictionary, keys is the cluewebid, values is a list of tuples (outlink, anchor-text)
    """

    # Check if ClueWeb API key is available, otherwise use Serper
    if not CLUEWEB_API_KEY or CLUEWEB_API_KEY == "YOUR_API_KEY":
        print("ClueWeb API key not available, using Serper search as fallback")
        return query_serper(query, num_docs)

    num_docs = str(num_docs)
    URL = "https://clueweb22.us"

    if with_url:
        request_url = f"{URL}/search?query={query}&k={num_docs}&with_outlink=True"
    else:
        request_url = f"{URL}/search?query={query}&k={num_docs}"

    headers = {"X-API-Key": CLUEWEB_API_KEY}

    try_count = 0
    while try_count <= num_tries:
        try:
            try_count += 1
            # print(f"Making API request to: {request_url}")
            response = requests.get(request_url, headers=headers)
        except Exception as e:
            print(f"Request failed with exception: {e}")
            if try_count < num_tries:
                print("Retrying")
                continue
            else:
                print("Reached max number of retries, returning empty data")
                if with_url:
                    return []
                else:
                    return [], []
        else:
            # print(f"Search works fine, status code: {response.status_code}")
            break

    # Check if the request was successful
    if response.status_code != 200:
        print(f"API request failed with status code: {response.status_code}")
        print(f"Response content: {response.text}")
        if with_url:
            return []
        else:
            return [], []

    # Check if response has content
    if not response.text.strip():
        print("API returned empty response")
        if with_url:
            return []
        else:
            return [], []

    try:
        json_data = response.json()
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        print(
            f"Response content: {response.text[:500]}..."
        )  # Print first 500 chars for debugging
        if with_url:
            return []
        else:
            return [], []

    results = json_data.get("results", [])
    return_cleaned_text = []
    num_docs_read = 0
    urls = []

    if with_url:
        outlinks = json_data.get("outlinks", [])
        for returned_document, returned_outlinks in zip(results, outlinks):
            decoded_result = base64.b64decode(returned_document).decode("utf-8")
            parsed_result = json.loads(
                decoded_result
            )  # keys: ['URL', 'URL-hash', 'Language', 'ClueWeb22-ID', 'Clean-Text']

            decoded_outlinks = base64.b64decode(returned_outlinks).decode("utf-8")
            parsed_outlinks = json.loads(
                decoded_outlinks
            )  # keys: ['url', 'urlhash', 'language', 'ClueWeb22-ID', 'outlinks']

            url = parsed_result["URL"].strip()
            cweb_id = parsed_result["ClueWeb22-ID"]
            text = parsed_result["Clean-Text"]

            if num_docs_read >= num_top_docs_to_read:
                if with_id:
                    return_cleaned_text.append((cweb_id, text, url))
                else:
                    return_cleaned_text.append((text, url))
            else:
                num_docs_read += 1
                valid_outlinks = []
                for outlink in parsed_outlinks["outlinks"]:
                    if outlink[-1] is not None and "clueweb22-en00" in outlink[-1]:
                        valid_outlinks.append(outlink)
                    updated_doc_text, exact_match_not_found, total = (
                        match_outlinks_to_doc(valid_outlinks, text)
                    )

                if with_id:
                    return_cleaned_text.append((cweb_id, updated_doc_text, url))
                else:
                    return_cleaned_text.append((updated_doc_text, url))

        return return_cleaned_text
    else:
        for returned_document in results:
            decoded_result = base64.b64decode(returned_document).decode("utf-8")
            parsed_result = json.loads(
                decoded_result
            )  # keys: ['URL', 'URL-hash', 'Language', 'ClueWeb22-ID', 'Clean-Text']

            url = parsed_result["URL"].strip()
            urls.append(url)
            cweb_id = parsed_result["ClueWeb22-ID"]
            text = parsed_result["Clean-Text"]
            if with_id:
                return_cleaned_text.append((cweb_id, url, text))
            else:
                return_cleaned_text.append(text)

    return return_cleaned_text, urls


def match_outlinks_to_doc(outlinks, doc_text):
    exact_match_not_found = 0
    not_matched_links = []
    for outlink in outlinks:
        url, urlhash, anchor_text, _, language, cweb_id = outlink
        idx = doc_text.find(anchor_text)
        if idx != -1:
            doc_text = (
                doc_text[:idx]
                + f"[{anchor_text}]({url})"
                + doc_text[idx + len(anchor_text) :]
            )
        else:
            exact_match_not_found += 1
            not_matched_links.append(f"[{anchor_text}]({url})")
    doc_text += (
        "Here are additional URLs and their anchor texts mentioned in this document:\n"
        + "\n".join(not_matched_links)
    )

    return doc_text, exact_match_not_found, len(outlinks)


def read_query_file(query_file):
    queries = []
    with open(query_file, "r", encoding="utf-8") as f:
        for line in f:
            queries.append(line.strip())
    return queries


if __name__ == "__main__":
    query = "name of reindeer in Frozen"
    # ret = query_clueweb(query, num_docs=10, num_top_docs_to_read=2, num_outlinks_per_doc=None, with_id=True, with_url=True)
    # for r in ret:
    #     print(r[1])

    # texts, outlinks = query_clueweb_with_outlinks(query, num_docs=1)
    # for id in outlinks:
    #     print(outlinks[id])
    #     break
    # debugging stuff
    # url = "https://www.svg.com/424956/disguised-toasts-transformation-is-turning-heads/"
    # url_hash = "AFDD3E7E501B9050EFAD110908885500"
    # cweb_id = "clueweb22-en0017-71-06754"
    # texts, outlinks = query_clueweb_url(url)

    # print(texts)
    # print(outlinks)
