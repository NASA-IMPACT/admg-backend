def extract_doi(concept):
    """test function to extract missing DOI metadata. I'm actually not sure if this is legit and we should check for errors"""

    doi = concept["umm"].get("DOI", {}).get("DOI", "")
    if not doi:
        try:
            doi = (
                concept["metadata"]["CollectionCitations"][0]["OtherCitationDetails"]
                .split("DOI: ")[1]
                .split(".org/")[1]
            )
        except:
            pass
    return doi


def process_data_product(dp):
    # this takes a single entry from the campaign metadata list
    metadata = {}
    metadata["concept_id"] = dp["meta"].get("concept-id")
    metadata["doi"] = extract_doi(dp)
    metadata["cmr_projects"] = dp["umm"].get("Projects")
    metadata["cmr_short_name"] = dp["umm"].get("ShortName")
    metadata["cmr_entry_title"] = dp["umm"].get("EntryTitle")
    metadata["cmr_dates"] = dp["umm"].get("TemporalExtents", [])
    metadata["cmr_plats_and_insts"] = dp["umm"].get("Platforms", [])

    return metadata


def process_metadata_list(metadata_list):
    processed_metadata_list = []
    for dp in metadata_list:
        processed_metadata_list.append(process_data_product(dp))

    return processed_metadata_list
