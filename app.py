import streamlit as st
from streamlit.components.v1 import iframe
from streamlit_cookies_manager import EncryptedCookieManager
from uuid import uuid4
import os 
from pathlib import Path
import json 
import pickle
import numpy as np
from nltk import sent_tokenize
import re
from urllib.parse import urlparse
import random

def init_cookies():

    cookies = EncryptedCookieManager(
        prefix = "fact-checking-user-study",
        password = st.secrets["COOKIE_PASSWORD"]
    )

    if not cookies.ready():
        st.stop()

    return cookies

def manage_participant_id(cookies):

    # create participant ID and store as cookie in the browser 
    # to make it stable across page reloads

    # 1. read pid query parameter if provided
    query_params = st.query_params
    if "pid" in query_params:
        pid = query_params["pid"]

        cookies["participant_id"] = pid
        cookies.save()

    # 2. else check in cookies
    elif "participant_id" in cookies:
        pid = cookies["participant_id"]

    # 3. else generate new pid and store as cookie
    else:
        pid = str(uuid4())
        cookies["participant_id"] = pid
        cookies.save()

    return pid, cookies

def setup_pages(claims, cookies):
 
    # setup page order: pre -> claims -> post (with claims in random order)

    # 1. check in cookies
    if "claim_order" in cookies:
        order = cookies["claim_order"]

    # 2. check in session_state
    elif "claim_order" in st.session_state:
        order = st.session_state.claim_order

    # 3. create order if it does not exist yet
    else:
        order = list(range(len(claims)))
        order = random.shuffle(order)

    # save in cookies and session_state
    cookies["claim_order"] = order 
    cookies.save()
    st.session_state.claim_order = order

    pages = ["pre"] + [("claim", i) for i in order] + ["post"]

    return pages

# page navigation helper functions
def next_page():
    st.session_state.current_page += 1

def prev_page():
    st.session_state.current_page -= 1

#### CSS #### 
background_color = st.get_option("theme.backgroundColor")
secondary_background_color = st.get_option("theme.secondaryBackgroundColor")
text_color = st.get_option("theme.textColor")
link_color = st.get_option("theme.linkColor")
secondary_link_color = "#6c757d"

# CSS for page layout
css_layout = f"""

.st-key-app-container {{
    background-color: {secondary_background_color};  
}}

.section-label {{
    font-weight: bold;
}}

.evidence-label {{
    font-weight: bold;
    margin: 0px 40px;
    text-decoration: underline;
}}

.claim {{
    margin: 20px 40px;
    background-color: {background_color};
    padding: 1.5rem;
    font-size: 1.1rem;
}}

.verdict {{
    color: white; 
    padding: 10px; 
    border-radius: 5px; 
    text-align: center; 
    font-weight: bold;
    margin: 10px 40px;
}}

.justification {{
    margin: 20px 40px 50px 40px;
    background-color: {background_color};
    padding: 1.5rem;
}}

.evidence-card {{
    background-color: {background_color};
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    margin-left: 40px;
    margin-right: 40px;
}}

.evidence-title {{
    font-weight: 600;
    margin-bottom: 0.5rem;
    font-size: 1.1rem;
}}

.evidence-title a {{
    text-decoration: none;
}}

.evidence-content {{
    margin-bottom: 1rem;
}}

.source-url a {{
    font-size: 0.8rem;
    color: {secondary_link_color};
    text-decoration: none;
}}

.back-link a {{
    font-size: 0.8rem;
    color: {link_color};
    text-decoration: none;
}}

.back-link {{
    text-align: right;
}}

sup {{
    color: #6c757d;
}}

.button {{
    background-color: {background_color};
    padding: 5px;
    font-weight: 600;
    border-radius: 5px;
    cursor: pointer;
    display: inline-block;
}}

.button:hover {{
    background-color: #cce6f8;
}}

.button-container {{
    margin-bottom: 30px;
    margin-right: 40px;
    text-align: right;
}}

"""

# CSS for citation tooltips
css_citation_tooltips = f"""

.citation-container {{
    position: relative;
}}

.citation {{
    color: {link_color};
    background-color: #e7f3ff;
    padding: 2px 0px 2px 1px;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
    position: relative;
    border: 1px solid #b3d9ff;
    transition: all 0.2s ease;
}}

.citation:hover {{
    background-color: #cce7ff;
    border-color: #66b3ff;
    transform: translateY(-1px);
}}

.tooltip {{
    visibility: hidden;
    position: absolute;
    background-color: #2c3e50;
    color: white;
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 14px;
    line-height: 1.4;
    max-width: 400px;
    width: max-content;
    z-index: 1000;
    opacity: 0;
    transition: opacity 0.3s, visibility 0.3s;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    border: 1px solid #34495e;
    
    /* Position tooltip above citation */
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    margin-bottom: 8px;
}}

.tooltip::after {{
    content: "";
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 6px solid transparent;
    border-top-color: #2c3e50;
}}

.citation:hover .tooltip {{
    visibility: visible;
    opacity: 1;
}}

.tooltip-content {{
    font-weight: normal;
    font-style: italic;
}}

.tooltip-header {{
    font-weight: bold;
    margin-bottom: 6px;
    color: #3498db;
}}

/* For highlighting the specific cited sentence */
.highlight {{
    font-weight: bold;
    font-size: 1rem;
}}

/* Responsive tooltip positioning */
@media (max-width: 768px) {{
    .tooltip {{
        max-width: 280px;
        font-size: 12px;
    }}
}}

"""

# CSS for highlighting the source sentence to which the user is linked by clicking on tooltip
css_highlighting = f"""

:target:not(#justification) {{
    animation: hightlight-flash 0.75s linear;
}}

@keyframes hightlight-flash {{
    0% {{
        background-color: {secondary_link_color};
        opacity: 0.1;
    }}
    50% {{
        background-color: {secondary_link_color};
        opacity: 0.3;
    }}
    100% {{
        background-color: {background_color};
    }}
}}

"""

st.html(f"<style>{css_layout}</style>")
st.html(f"<style>{css_citation_tooltips}</style>")
st.html(f"<style>{css_highlighting}</style>")

#### CSS END #### 


## helper functions
# function for getting the path to the results directory (/fc_results) (different for local and Google Colab)
def get_results_dir():

    working_dir = Path(os.getcwd())

    return working_dir / "fc_results"

def load_json(filepath):

    with open(filepath, "r") as f:
        data = json.load(f)

    return data

def load_pickle(filepath):

    with open(filepath, "rb") as f:
        data = pickle.load(f)

    return data

def split_in_sentences(text):

    sentences = sent_tokenize(text)

    return sentences

def get_domain_name(url):

    if '://' not in url:
        url = 'http://' + url

    domain = urlparse(url).netloc

    # remove leading "www."
    domain = domain.replace("www.", "")

    return domain 

def cite_sentence(attribution, min_abs_thresh=5, max_ratio_thresh=0.3, max_citations=3):
    """
    Return indices of the context sources to cite
    based on the attribution scores.

    Thresholding: cite sources above a minimum absolute threshold
    and all sources (up to a maximum number) with at least attribution
    score of k% of the maximum score.
    """

    max_score = np.max(attribution)

    # thresholding
    citations = np.asarray((attribution >= min_abs_thresh) & (attribution >= (max_score*max_ratio_thresh))).nonzero()[0]

    # sort citations based on attribution score
    citations = np.array(sorted(citations, key=lambda x: attribution[x], reverse=True))

    # keep top-n citations
    citations = citations[:max_citations]

    return citations


## justification formatting ##
def add_answer_attributions(justification, attributions):

    citations = [cite_sentence(attr) for attr in attributions]   # get list of length of the number of sentences with the indices of sources to cite per sentence

    citations = [cite + 1 for cite in citations]   # adjust source indices starting from 1

    # remove citations from the justification text that might have been produced by the LLM to avoid confusion
    citation_pattern = r"\s*\[\d+([,\s]*\d+)*\]+"
    justification = re.sub(citation_pattern, "", justification)

    sentences = split_in_sentences(justification)

    justification_attributed = ""

    for sent, cite in zip(sentences, citations):

        start_idx = justification.find(sent)
        end_idx = start_idx + len(sent)

        if sent[-1] == ".": # check if the sentence ends with a period
            end_idx -= 1

        if len(cite) > 0:
            cite_str = " "
            for c in cite:
                cite_str += f"[{c}]"
        else:
            cite_str = ""

        justification_attributed += justification[start_idx:end_idx]
        justification_attributed += cite_str
        justification_attributed += ". "

    return justification_attributed

def get_evidence_tooltip_texts(claim, claim_idx, result_path):

    context_sources = claim['context_sources']
    evidence_paragraphs = claim['top_evidence_docs']
    page_idxs = claim['top_evidence_idxs']

    src2evd = {}

    j = 0
    for i, src in enumerate(context_sources, start=1):
        while(src not in evidence_paragraphs[j]):
            j += 1
        src2evd[i] = j


    # build tooltip texts by appending some context to the source sentence, with the source sentence being highlighted
    tooltip_texts = {}
    for source_idx, source_text in enumerate(context_sources, start=1):

        # get index of the evidence web page corresponding to the source
        evd_idx = src2evd[source_idx]
        page_idx = page_idxs[evd_idx]

        # build path to the complete web page with the evidence and read the text
        evidence_path = result_path / f"Web_Evidence/claim_{claim_idx}/search_result_{page_idx}.txt"
        lines = []
        with open(evidence_path, "r") as f:
            for i, line in enumerate(f):
                if i > 0:
                    lines.append(line.strip())
        evidence_text = " ".join(lines)

        # ## first version ##
        # # find original source in the complete evidence text
        # start_idx = evidence_text.find(source_text)
        # end_idx = start_idx + len(source_text)

        # context_len = 300   # how much context to add to the original source sentence
        # pre_context = evidence_text[max(0, start_idx-context_len):start_idx]
        # post_context = evidence_text[end_idx:min(len(evidence_text), end_idx+context_len)]
        # ##

        ## other version with complete sentences ##
        # split evidence text in sentences
        evidence_sentences = split_in_sentences(evidence_text)

        # get all start indices of all sentences in the evidence text
        sent_start_idxs = np.array([evidence_text.find(sent) for sent in evidence_sentences])
        sent_end_idxs = sent_start_idxs + np.array([len(sent) for sent in evidence_sentences])

        # find source sentence in the complete evidence text
        source_start_idx = evidence_text.find(source_text)
        source_end_idx = source_start_idx + len(source_text)

        ## since the source sentences come from the ContextCite package they are somehow not 100% identical to the sentences we get
        # by using nltk.sent_tokenize() even though in the package they use the same tokenizer
        # therefore we have to find the corresponding sentence boundaries here

        # find corresponding sentence start idx by taking the largest of the sent_start_idxs that is less or equal the source_start_idx
        sent_start_idx = sent_start_idxs[np.where(sent_start_idxs <= source_start_idx)[0][-1]]

        # find corresponding sentence end idx by taking the smallest of the sent_end_idxs that is greater or equal the source_end_idx
        sent_end_idx = sent_end_idxs[np.where(sent_end_idxs >= source_end_idx)[0][0]]

        # extend to the pre- and post-context (specified number of complete sentences)
        n_pre_sentences = 2
        n_post_sentences = 3

        # get start and end idxs of the whole tooltip text
        start_idx = sent_start_idxs[max(0, sent_start_idxs.tolist().index(sent_start_idx) - n_pre_sentences)]
        end_idx = sent_end_idxs[min(len(sent_end_idxs)-1, sent_end_idxs.tolist().index(sent_end_idx) + n_post_sentences)]

        pre_context = evidence_text[start_idx:source_start_idx]
        post_context = evidence_text[source_end_idx:end_idx]
        ##

        # escape html syntax
        pre_context = pre_context.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
        post_context = post_context.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
        source_text = source_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')

        source_text_highlighted = f"<span class='highlight'>{source_text}</span>"

        tooltip_text = "".join(["... ", pre_context, source_text_highlighted, post_context, " ..."])

        tooltip_texts[str(source_idx)] = tooltip_text

    return tooltip_texts

def build_justification_html(claim, claim_idx, result_path, experiment_group):

    # helper function for tooltips (experiment group 2)
    def get_tooltip_html(re_match):

        citation_idx = re_match.group(1)
        tooltip_text = evidence_texts[citation_idx]

        citation_id = f"citation-{citation_idx}"

        html = f"""<a class='citation' id='{citation_id}' style='text-decoration: none;' href='#source-{citation_idx}'>
            [{citation_idx}]
            <div class='tooltip'>
                <div class='tooltip-header'>Evidence [{citation_idx}]:</div>
                <div class='tooltip-content'>"{tooltip_text}"</div>
            </div>
        </a>
        """

        return html
    
    justification = claim['predictions']['justification']
    
    if experiment_group == 1:

        return justification

    elif experiment_group == 2:

        # load answer attributions
        attr_path = result_path / f"Answer_Attributions/claim_{claim_idx}/answer_attributions_np.pkl"
        attributions = load_pickle(attr_path)

        # get justification text with answer attributions (added to the text as citations in brackets, e.g. [1])
        justification = add_answer_attributions(justification, attributions)

        # load evidence texts that should be displayed for each citation 
        evidence_texts = get_evidence_tooltip_texts(claim, claim_idx, result_path)

        # replace html characters
        justification = justification.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')

        # replace citations with html code to render the tooltip when hovering
        cite_pattern = r"\[(\d+)\]"
        justification_html = re.sub(cite_pattern, get_tooltip_html, justification)

        # put together with css
        justification_with_tooltips = f"""
        <span class='citation-container'>
            {justification_html}
        </span>
        """

        return justification_with_tooltips

    elif experiment_group == 3:

        pass

## justification formatting end ##

## evidence formatting ##
def build_sources_html(claim, claim_idx, result_path, experiment_group):

    context_sources = claim['context_sources']
    evidence_paragraphs = claim['top_evidence_docs']
    evidence_urls = claim['top_evidence_urls']

    ## load search infos of the top evidence paragraphs
    page_idxs = [int(idx) for idx in claim['top_evidence_idxs']]
    all_search_infos = load_json(result_path / f"Web_Evidence/claim_{claim_idx}/search_infos.json")
    search_infos = [all_search_infos[idx-1] for idx in page_idxs]     # page_idxs start with 1 not with 0, therefore use idx-1 !

    # get mapping from context source to the 
    # corresponding evidence paragraphs that the source is from
    src2evd = {}

    j = 0
    for i, src in enumerate(context_sources, start=1):
        while(src not in evidence_paragraphs[j]):
            j += 1
        src2evd[i] = j

    # get mapping from evidence paragraphs to all context sources it contains
    evd2srcs = {}
    j = 0
    for i, src in enumerate(context_sources):
        while(src not in evidence_paragraphs[j]):
            j += 1

        if not evd2srcs.get(j, None): 
            evd2srcs[j] = []
        evd2srcs[j].append(i)

    ## evidence sources, formatted depending on the experiment group
    evidence_html = ""

    if experiment_group == 1: # complete paragraphs without citation indices
        for evidence_paragraph, search_info in zip(evidence_paragraphs, search_infos):

            url = search_info['url']
            title = search_info['title']

            evidence_html += f"""
                <div class="evidence-card">
                    <div class="evidence-title">
                        <a href='{url}' target='_blank'>{title}</a>
                    </div>
                    <div class="evidence-content">... {evidence_paragraph} ...</div>
                    <div class="source-url">
                        <a href='{url}' target='_blank'>{url}</a>
                    </div>
                    <div class="back-link">
                        <a href="#justification">Back to Justification</a>
                    </div>
                </div>
            """


    if experiment_group == 2:   # sentences with citation indices

        for i, (evidence_paragraph, search_info) in enumerate(zip(evidence_paragraphs, search_infos)):

            url = search_info['url']
            title = search_info['title']

            # build evidence paragraph with sentence numbers for citing
            src_idxs = evd2srcs[i]

            evidence_paragraph_with_numbering = ""
            for src_idx in src_idxs:
                evidence_paragraph_with_numbering += f"<span id='source-{src_idx+1}'><sup>[{src_idx+1}]</sup> {context_sources[src_idx]} </span>"

            evidence_html += f"""
                <div class="evidence-card">
                    <div class="evidence-title">
                        <a href='{url}' target='_blank'>{title}</a>
                    </div>
                    <div class="evidence-content">... {evidence_paragraph_with_numbering} ...</div>
                    <div class="source-url">
                        <a href='{url}' target='_blank'>{url}</a>
                    </div>
                    <div class="back-link">
                        <a href="#justification">Back to Justification</a>
                    </div>
                </div>
            """

            
    return evidence_html

## evidence formatting end ##


def main():

    cookies = init_cookies()

    # --- get or create participant ID ---
    pid = manage_participant_id(cookies)
    st.write(f"Participant ID: {pid}")

    # --- initialize current page to display ---
    if "current_page" not in st.session_state:
        st.session_state.current_page = 0

    # --- load the data (claims + results) from the pipeline and setup page order ---
    claims = load_json("data/results.json")

    pages = setup_pages(claims, cookies)
    st.write(pages)

    st.title("Fact-checking User Study")


    st.write("Pre-study Survey")
    iframe(f"https://jonas-peschel.github.io/fact-checking-surveys/pre/?pid={pid}&claim=pre", height=1000)

    st.write("Per-claim Survey")
    iframe(f"https://jonas-peschel.github.io/fact-checking-surveys/claim/?pid={pid}&claim={100}", height=1000)

    st.write("Post-study Survey")
    iframe(f"https://jonas-peschel.github.io/fact-checking-surveys/post/?pid={pid}&claim=post", height=1000)


if __name__ == "__main__":

    main()