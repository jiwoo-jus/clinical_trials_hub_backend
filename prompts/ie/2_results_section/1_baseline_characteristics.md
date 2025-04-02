# CONTEXT #
You are tasked with analyzing clinical trial study reports or papers to extract specific information as structured data. Omit any fields if the corresponding data does not exist in the target articles. Do not invent or assume information that is not present in the given content.
# PAPER CONTENT #
{{pmc_text}}

# TARGET #
Extract the baselineCharacteristicsModule of the study.
# RESPONSE #
The JSON response must adhere to the following structure, where each field is annotated with its expected type.
Ensure that the output is a valid and correctly formatted JSON string.
Format:
```json
{
    "baselineCharacteristicsModule": {  // Baseline demographic and other initial measures, by arm/group.
        "populationDescription": "value",   // Brief reason or explanation if baseline participants differ from the assigned groups.
        "typeUnitsAnalyzed": "value",   // (Optional) If units are not participants (e.g., eyes, lesions).
        "groups": [// ARRAY of OBJECT. Arms/groups for baseline assessment. Must include a "Total" group as the last entry.
            {
                "id": "value",             // BG000 is the first group, BG001 is the second, and so on.
                "title": "value",          // Short label that identifies the group (e.g., "Placebo," "Treatment A", "Total").
                "description": "value"     // Brief explanation of the group's characteristics or interventions.
            }
        ],
        "denoms": [// ARRAY of OBJECT. Structure for Overall Baseline Measure Data (Row). 
            {
                "units": "value",          // Unit of measure for the data in this row. Default is "Participants".
                "counts": [ // ARRAY of OBJECT. Each object represents a group and its corresponding count in the same order as the "groups" array.
                    {
                        "groupId": "value",    // References an ID from the "groups" array. (e.g., "BG000," "BG001," "BG002").
                        "value": "value"       // Number of participants in this group.
                    }
                ]
            }
        ],
        "measures": [// ARRAY of OBJECT. Each baseline or demographic characteristic. Required baseline measures include Age, Sex/Gender, Race, Ethnicity (if applicable), and any other measures.
            {
                "title": "value",
                // Required1: Age => ENUM("Age, Continuous", "Age, Categorical", "Age, Customized")
                // Required2: Sex/Gender => ENUM("Sex: Female, Male", "Sex/Gender, Customized")
                // Required3 (if possible): Race and Ethnicity => ENUM("Race (NIH/OMB)", "Ethnicity (NIH/OMB)", "Race/Ethnicity, Customized", "Race and Ethnicity Not Collected")
                // Required4 (if possible): Region of Enrollment => ENUM("Region of Enrollment")
                // (Optional): Any other measures
                "description": "value", // Additional descriptive information about the baseline measure
                "populationDescription": "value",   // (Optional) If the analyzed population differs from the overall baseline population.
                "paramType": "value",   // The type of data for the baseline measure. ENUM("COUNT_OF_PARTICIANTS","MEAN","NUMBER","MEDIAN","COUNT_OF_UNITS,"GEOMETRIC_MEAN","LEAST_SQUAES_MEAN","LOG_MEN","GEOMETRIC_LEAST_SQUAES_MEAN")
                "dispersionType": "value",  // Baseline Measure Dispersion/Precision. ENUM("STANDARD_DEVIATION","FULL_RANGE","INTER_QUARTILE_RANGE","NA","CONFIDENCE_80","CONFIDENCE_90","CONFIDENCE_95","CONFIDENCE_975","CONFIDENCE_99","CONFIDENCE_OTHER","GEOMETRIC_COEFFICIENT""STANDARD_ERROR")
                "unitOfMeasure": "value",   // e.g., "Participants", "years", "kg", etc.
                "denoms": [// ARRAY of OBJECT. Same structure as "denoms" above, if needed for measure-specific denominators.
                    {
                        "units": "value",
                        "counts": [// ARRAY of OBJECT. 
                            {
                                "groupId": "value",
                                "value": "value"
                            }
                        ]
                    }
                ],
                "classes": [// ARRAY of OBJECT. Within each measure, define rows or classifications.
                    {
                        "title": "value", // Baseline RowTitle. (e.g, "Sex: Female, Male")
                        "denoms": [// ARRAY of OBJECT. Same structure as "denoms" above, if needed for class-specific counts.
                            {
                                "units": "value",
                                "counts": [// ARRAY of OBJECT. 
                                    {
                                        "groupId": "value",
                                        "value": "value"
                                    }
                                ]
                            }
                        ],
                        "categories": [ // ARRAY of OBJECT. Each category is essentially a sub-row under the class.
                            {
                                "title": "value",   // e.g., "Female", "Hispanic or Latino"
                                "measurements": [   // ARRAY of OBJECT. Data for each group in this category.
                                    {
                                        "groupId": "value", // e.g., "BG000"
                                        "value": "value",   // e.g., "53", "64.4"
                                        "spread": "value",   // e.g., "9.4" (for SD), or omitted if not applicable.
                                        "lowerLimit": "value", // e.g., "5.6"  Based on Measure Type and Measure of Dispersion (e.g., lower limit of Full Range).
                                        "upperLimit": "9.9" // e.g., "9.9"  Based on Measure Type and Measure of Dispersion (e.g., upper limit of Full Range)
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
}
```