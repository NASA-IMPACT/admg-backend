def extract_doi(concept):
    """test function to extract missing DOI metadata.
    I'm actually not sure if this is legit and we should check for errors"""

    doi = concept["umm"].get("DOI", {}).get("DOI", "")
    if not doi:
        try:
            doi = (
                concept["metadata"]["CollectionCitations"][0]["OtherCitationDetails"]
                .split("DOI: ")[1]
                .split(".org/")[1]
            )
        except Exception:
            pass
    return doi


def process_data_product(dp):
    # this takes a single entry from the campaign metadata list
    return {
        "concept_id": dp["meta"].get("concept-id"),
        "doi": extract_doi(dp),
        "cmr_projects": dp["umm"].get("Projects"),
        "cmr_short_name": dp["umm"].get("ShortName"),
        "cmr_entry_title": dp["umm"].get("EntryTitle"),
        "cmr_dates": dp["umm"].get("TemporalExtents", []),
        "cmr_plats_and_insts": dp["umm"].get("Platforms", []),
        "cmr_science_keywords": dp["umm"].get("ScienceKeywords", {}),
        "cmr_abstract": dp["umm"].get("Abstract", ''),
        "cmr_data_formats": [
            info.get('Format', '')
            for info in dp["umm"]
            .get('ArchiveAndDistributionInformation', {})
            .get('FileDistributionInformation', [{}])
        ],
    }


def process_metadata_list(metadata_list):
    return [process_data_product(dp) for dp in metadata_list]
