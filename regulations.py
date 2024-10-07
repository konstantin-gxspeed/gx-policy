import xml.etree.ElementTree as ET
import ollama
import requests
from utils.xml_parser import get_branch


def get_data(title, part, latest_issue_date):
    part_xml = requests.get(
        f"https://www.ecfr.gov/api/versioner/v1/full/{latest_issue_date}/title-{title}.xml?part={part}")
    regulation_content = []
    xml_data = part_xml.content
    if (part_xml.content):
        tree = ET.fromstring(xml_data)
        raw_string = ET.tostring(tree, encoding='utf-8', method='text')
        abstract = ollama.generate(
            model='llama3', prompt=f'only output actual result and Give me abstract for this file {raw_string}')['response']

        get_branch(tree=tree, regulations=regulation_content)
        reg_title = tree.find('HEAD').text
    return {
        "reg_title": reg_title,
        "content": regulation_content,
        "abstract": abstract,
        "raw_string": raw_string,
        "regulation_content": regulation_content
    }
