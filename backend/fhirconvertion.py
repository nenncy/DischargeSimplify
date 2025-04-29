import os
import json
import requests
from datetime import datetime
from typing import Optional
from fhir.resources.composition import Composition

FHIR_AUTHOR_REF = os.getenv("FHIR_AUTHOR_REF", "Device/DischargeSimplify")

def fetch_simplified_json(simplify_url: str, raw_text: str) -> dict:
    """
    POST raw_text to the simplify endpoint and return the parsed JSON response.
    """
    resp = requests.post(
        simplify_url,
        json={"raw_text": raw_text},
        timeout=60
    )
    resp.raise_for_status()
    return resp.json()


def convert_to_composition(data: dict, patient_id: str, author_reference: Optional[str] = None) -> Composition:
    """
    Convert the simplified JSON structure into a FHIR Composition resource.
    """
    from datetime import datetime
    ref = author_reference or FHIR_AUTHOR_REF
    comp_dict = {
        "resourceType": "Composition",
        "status": "final",
        "type": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "11502-2",
                "display": "Discharge summary"
            }]
        },
        "subject": [ { "reference": f"Patient/{patient_id}" } ],
        "date": datetime.now().astimezone().isoformat(),
        "author": [ { "reference": ref } ],
        "title": "Discharge Summary",
        "section": []
    }

    # Summary section (note lowercase key)
    summary_text = data.get("Summary") or data.get("summary") or ""
    comp_dict["section"].append({
        "title": "Summary",
        "text": {
            "status": "generated",
            "div": f"<div>{summary_text}</div>"
        }
    })

    # And for lists:
    list_mappings = [
        ("instructions", "Instructions"),
        ("importance",  "Importance"),
        ("follow_up",   "FollowUpTasks"),
        ("medications", "Medications"),
        ("precautions", "Precautions"),
        ("references",  "References"),
    ]
    for key, title in list_mappings:
        items = data.get(key, [])
        if items:
            html = "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"
            comp_dict["section"].append({
                "title": title,
                "text": {"status": "generated", "div": html}
            })

    # Disclaimer (lowercase)
    disclaimer = data.get("disclaimer", "")
    if disclaimer:
        comp_dict["section"].append({
            "title": "Disclaimer",
            "text": {"status": "generated", "div": f"<div>{disclaimer}</div>"}
        })

    return Composition(**comp_dict)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch simplified JSON and convert to FHIR Composition"
    )
    parser.add_argument(
        "--simplify-url", 
        default=os.getenv("SIMPLIFY_URL", "http://localhost:8000/simplify"),
        help="URL of the simplify endpoint"
    )
    parser.add_argument(
        "--text-file", 
        required=True,
        help="Path to the raw discharge instructions text file"
    )
    parser.add_argument(
        "--patient-id", 
        required=True,
        help="FHIR Patient ID to reference in the Composition"
    )
    parser.add_argument(
        "--output-file", 
        help="Optional path to write the resulting FHIR JSON"
    )
    args = parser.parse_args()

    # Read raw text
    with open(args.text_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Fetch simplified JSON
    simplified = fetch_simplified_json(args.simplify_url, raw_text)

    # Convert to FHIR Composition
    composition = convert_to_composition(simplified, args.patient_id)

    # Serialize to JSON
    fhir_json = composition.dict()

    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as out:
            json.dump(fhir_json, out, indent=2)
        print(f"FHIR Composition written to {args.output_file}")
    else:
        print(json.dumps(fhir_json, indent=2))


if __name__ == "__main__":
    main()
