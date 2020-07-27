{
    "PlatformType": {
        "short_name": {
            "type": "CharField",
            "max_length":256, 
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length":512, 
            "required": False
        },
        "notes_public": {
            "type": "TextField",
            "required": False
        },
        "foreign-platform_type-short_name": {
            "type": "ForeignKey",
            "required": False
        },       
        "gcmd_uuid": {
            "type": "UUIDField",
            "required": False
        },
        "example": {
            "type": "CharField",
            "max_length":256, 
            "required": False
        },
    },
    "NasaMission": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "notes_public": {
            "type": "TextField",
            "required": False
        }
    "InstrumentType": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "notes_public": {
            "type": "TextField",
            "required": False
        },
        "foreign-platform_type-short_name": {
            "type": "ForeignKey",
            "required": False
        },
        "gcmd_uuid": {
            "type": "UUIDField",
            "required": False
        },
        "example": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
    },
    "HomeBase": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "notes_public": {
            "type": "TextField",
            "required": False
        },
        "location": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "additional_info": {
            "type": "CharField",
            "max_length": 204,
            "required": False
        }
    },
    "FocusArea": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "notes_public": {
            "type": "TextField",
            "required": False
        },
        "url": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        }
    },
    "Season": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "notes_public": {
            "type": "TextField",
            "required": False
        },
    },

    "Repository": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "notes_public": {
            "type": "TextField",
            "required": False
        },
        "gcmd_uuid": {
            "type": "UUID",
            "required": False
        }
    },
    "MeasurementRegion": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "notes_public": {
            "type": "TextField",
            "required": False
        },
        "gcmd_uuid": {
            "type": "UUID",
            "required": False
        },
        "example": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        }
    },
    "GeographicalRegion": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "notes_public": {
            "type": "TextField",
            "required": False
        },
        "gcmd_uuid": {
            "type": "UUID",
            "required": False
        },
        "example": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        }
    },
    "GeophysicalConcept": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "notes_public": {
            "type": "TextField",
            "required": False
        },
        "gcmd_uuid": {
            "type": "UUID",
            "required": False
        },
        "example": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        }
    },
    "PartnerOrg": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "notes_public": {
            "type": "TextField",
            "required": False
        },
        "website": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        }
    },
    "Alias": {
        "content_type": {
            "type": "ForeignKey",
            "required": True
        },
        "object_id": {
            "type": "UUIDField",
            "required": True
        },
        "parent_fk": {
            "type": "GenericForeignKey",
            "required": True
        },
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "source": {
            "type": "CharField",
            "max_length": 204,
            "required": False
        }
    },
    "GcmdProject": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "bucket": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "gcmd_uuid": {
            "type": "UUID",
            "required": True
        }
    },
    "GcmdInstrument": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "instrument_category": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "instrument_class": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "instrument_type": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "instrument_subtype": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "gcmd_uuid": {
            "type": "UUID",
            "required": True
        }
    },
    "GcmdPlatform": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "category": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "series_entry": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },      
        "description": {
            "type": "TextField",
            "required": False
        },
        "gcmd_uuid": {
            "type": "UUID",
            "required": True
        }
    },
    "GcmdPhenomena": {
        "category": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "topic": {    
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "term": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "variable_1": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "variable_2": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "variable_3": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "gcmd_uuid": {
            "type": "UUID",
            "required": True
        }
    },
    "Campaign": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "notes_internal":
            "type": "TextField",
            "required": False
        },
        "notes_public": {
            "type": "TextField",
            "required": False
        },
        "description_short": {
            "type": "TextField",
            "required": False
        },
        "description_long": {
            "type": "TextField",
            "required": False
        },
        "focus_phenomena": {
            "type": "CharField",
            "max_length": 1024,
            "required": True
        },
        "region_description": {
            "type": "TextField",
            "required": True
        },
        "spatial_bounds": {
            "type": "PolygonField",
            "required": False
        },
        "start_date": {
            "type": "DateField",
            "required": True
        },
        "end_date": {
            "type": "DateField",
            "required": False
        },
        "funding_agency": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "funding_program": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "funding_program_lead": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "lead_investigator": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "technical_contact": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "number_collection_periods": {
            "type": "PositiveIntegerField",
            "required": True
        },
        "doi": {
            "type": "CharField",
            "max_length": 1024,
            "required": False
        },
        "number_data_products": {
            "type": "PositiveIntegerField",
            "required": False
        },
        "data_volume": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "repository_website": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "project_website": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "tertiary_website": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "publication_links": {
            "type": "CharField",
            "max_length": 204,
            "required": False
        },
        "other_resources": {
            "type": "CharField",
            "max_length": 204,
            "required": False
        },
        "ongoing": {
            "type": "Boolean",
            "required": True
        },
        "nasa_led": {
            "type": "Boolean",
            "required": True
        },
        "table-nasa_mission-short_name": {
            "type": "ManyToManyField",
            "required": False
        },
        "table-focus_area-short_name": {
            "type": "ManyToManyField",
            "required": True
        },
        "table-season-short_name": {
            "type": "ManyToManyField",
            "required": True
        },
        "table-repositorie-short_name": {
            "type": "ManyToManyField",
            "required": True
        },
        "table-platform_type-short_name": {
            "type": "ManyToManyField",
            "required": True
        },
        "table-partner_org-short_name": {
            "type": "ManyToManyField",
            "required": False
        },
        "table-gcmd_phenomena-ignore_code": {
            "type": "ManyToManyField",
            "required": True
        },
        "table-gcmd_project-gcmd_uuid": {
            "type": "ManyToManyField",
            "required": False
        },
        "table-geophysical_concepts-short_name": {
            "type": "ManyToManyField",
            "required": True
        }
    },
    "Platform": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "notes_internal":
            "type": "TextField",
            "required": False
        },
        "notes_public":
            "type": "TextField",
            "required": False
        },
        "foreign-platform_type-short_name": {
            "type": "ForeignKey"
            "required": False
        },
        "image": {
            "type": "ForeignKey",
            "required": False
        },
        "description":
            "type": "TextField",
            "required": True
        },
        "online_information": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "stationary": {
            "type": "BooleanField",
            "required": True
        },
        "table-gcmd_platform-gcmd_uuid": {
            "type": "ManyToManyField",
            "required": False
        }
    },
    "Instrument": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "notes_internal":
            "type": "TextField",
            "required": False
        },
        "notes_public":
            "type": "TextField",
            "required": False
        },
        "description":
            "type": "TextField",
            "required": True
        },
        "lead_investigator": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "technical_contact": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "facility": {       
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "funding_source": {
            "type": "CharField",
            "max_length": 256,
            "required": False
        },
        "spatial_resolution": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "temporal_resolution": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },      
        "radiometric_frequency": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "calibration_information": {
            "type": "CharField",
            "max_length": 1024,
            "required": False
        },
        "instrument_manufacturer": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "overview_publication": {
            "type": "CharField",
            "max_length": 2048,
            "required": False
        },
        "online_information": {
            "type": "CharField",
            "max_length": 204,
            "required": False
        },
        "instrument_doi": {
            "type": "CharField",
            "max_length": 1024,
            "required": False
        },
        "table-gcmd_instrument-short_name": {
            "type": "ManyToManyField",
            "required": False
        },
        "table-instrument_type-short_name": {
            "type": "ManyToManyField",
            "required": True
        },
        "table-gcmd_phenomena-short_name": {
            "type": "ManyToManyField",
            "required": True
        },
        "table-measurement_region-short_name": {
            "type": "ManyToManyField",
            "required": True
        },
        "table-repository-short_name": {
            "type": "ManyToManyField",
            "required": False
        },
        "table-geophysical_concept-short_name": {
            "type": "ManyToManyField",
            "required": True
        },
    },
    "Deployment": {
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "long_name": {
            "type": "CharField",
            "max_length": 512,
            "required": False
        },
        "notes_internal": {
            "type": "TextField",
            "required": False
        },
        "notes_public": {
            "type": "TextField",
            "required": False
        },
        "foreign-campaign-short_name" : {
            "type": "ForeignKey",
            "required": True
        },
        "ignore_study_region_map" : {
            "type": "ForeignKey",
            "required": False
        },
        "ignore_ground_sites_map" : {
            "type": "ForeignKey",
            "required": False
        },
        "ignore_flight_tracks" : {
            "type": "ForeignKey",
            "required": False
        },
        "start_date": {
            "type": "DateField",
            "required": True
        },
        "end_date": {
            "type": "DateField",
            "required": True
        },
        "number_collection_periods": {
            "type": "PositiveIntegerField",
            "required": False
        },
        "table-geographical_region-short_name": {
            "type": "ManyToManyField",
            "required": True
        }
    },
    "IopSe": {
        "foreign-deployment-short_name": {
            "type": "ForeignKey",
            "required": True
        },
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },
        "start_date": {
            "type": "DateField",
            "required": True
        },
        "end_date": {
            "type": "DateField",
            "required": True
        },
        "description": {
            "type": "TextField",
            "required": True
        },
        "region_description": {
            "type": "TextField",
            "required": True
        },
        "published_list": {
            "type": "CharField",
            "max_length": 1024,
            "required": False
        },
        "reports": {
            "type": "CharField",
            "max_length": 1024,
            "required": False
        },
        "reference_file": {
            "type": "CharField",
            "max_length": 1024,
            "required": False
        }
    },
    "IOP": {
        "foreign-deployment-short_name": {
            "type": "ForeignKey",
            "required": True
        },
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required":         
        "start_date": {
            "type": "DateField",
            "required": True
        },
        "end_date": {
            "type": "DateField",
            "required": True
        },
        "description": {
            "type": "TextField",
            "required": True
        },
        "region_description": {
            "type": "TextField",
            "required": True
        },
        "published_list": {
            "type": "CharField",
            "max_length": 1024,
            "required": False
        },
        "reports": {
            "type": "CharField",
            "max_length": 1024,
            "required": False
        },
        "reference_file": {
            "type": "CharField",
            "max_length": 1024,
            "required": False
        }
    },
    "SignificantEvent": {
        "foreign-deployment-short_name": {
            "type": "ForeignKey",
            "required": True
        },
        "short_name": {
            "type": "CharField",
            "max_length": 256,
            "required": True
        },     
        "start_date": {
            "type": "DateField",
            "required": True
        },
        "end_date": {
            "type": "DateField",
            "required": True
        },
        "description": {
            "type": "TextField",
            "required": True
        },
        "region_description": {
            "type": "TextField",
            "required": True
        },
        "published_list": {
            "type": "CharField",
            "max_length": 1024,
            "required": False
        },
        "reports": {
            "type": "CharField",
            "max_length": 1024,
            "required": False
        },
        "reference_file": {
            "type": "CharField",
            "max_length": 1024,
            "required": False
        },
        "foreign-iop-short_name": {
            "type": "ForeignKey",
            "required": False
        }
    },
    "CollectionPeriod": {
        "foreign-deployment-short_name": {
            "type": "ForeignKey",
            "required": True
        },
        "foreign-platform-short_name": {
            "type": "ForeignKey",
            "required": True
        },
        "asp_long_name": {
            "type": "CharField",
            "max_length": 512,
            "required":False
        },
        "platform_identifier": {
            "type": "CharField",
            "max_length": 128,
            "required":False
        },
        "home_base": {
            "type": "CharField",
            "max_length": 256,
            "required":False
        },
        "campaign_deployment_base": {
            "type": "CharField",
            "max_length": 256,
            "required":False
        },
        "platform_owner": {
            "type": "CharField",
            "max_length": 256,
            "required":False
        },
        "platform_technical_contact": {
            "type": "CharField",
            "max_length": 256,
            "required":False
        },
        "instrument_information_source": {
            "type": "CharField",
            "max_length": 1024,
            "required": False
        },
        "notes_internal": {
            "type": "TextField",
            "required": False
        },
        "notes_public": {
            "type": "TextField",
            "required": False
        },
        "num_ventures": {
            "type": "TextField",
            "required": False
        },
        "auto_generated": {
            "type": "Boolean",
            "required": True
        },
        "table-instrument-short_name": {
            "type": "ManyToManyField",
            "required": True
        },
    }
