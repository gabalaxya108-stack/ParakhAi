from typing import List
from backend.app.schemas.rules import RuleDefinition, RuleSeverity
from backend.app.schemas.extraction import DeclarationType

CODIFIED_RULES: List[RuleDefinition] = [
    RuleDefinition(
        rule_id="LMR-R06-01",
        legal_reference="Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011",
        title="Name and Address of Manufacturer / Packer / Importer",
        description="Every package shall bear the name and complete address of the manufacturer, or where manufacturer is not the packer, the name and complete address of manufacturer and packer.",
        severity=RuleSeverity.CRITICAL,
        target_declaration=DeclarationType.NAME_AND_ADDRESS,
        penalty_section="Section 36(1), Legal Metrology Act, 2009 (Fine up to ₹25,000 for first offence)"
    ),
    RuleDefinition(
        rule_id="LMR-R06-02",
        legal_reference="Rule 6(1)(b), Legal Metrology (Packaged Commodities) Rules, 2011",
        title="Generic or Common Name of Commodity",
        description="The common or generic names of the commodity contained in the package shall be prominently displayed on the Principal Display Panel.",
        severity=RuleSeverity.MAJOR,
        target_declaration=DeclarationType.GENERIC_NAME,
        penalty_section="Section 36(1), Legal Metrology Act, 2009"
    ),
    RuleDefinition(
        rule_id="LMR-R06-03",
        legal_reference="Rule 6(1)(c) & Rule 13, Legal Metrology (Packaged Commodities) Rules, 2011",
        title="Net Quantity Declaration in Standard SI Units",
        description="The net quantity in terms of standard unit of weight or measure (g, kg, ml, l) shall be declared. Use of non-standard symbols like 'gms', 'gm', 'kilos', 'litres', 'ltr' is strictly prohibited.",
        severity=RuleSeverity.CRITICAL,
        target_declaration=DeclarationType.NET_QUANTITY,
        penalty_section="Section 36(1) & Rule 13, Legal Metrology (PC) Rules, 2011"
    ),
    RuleDefinition(
        rule_id="LMR-R06-04",
        legal_reference="Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011",
        title="Month and Year of Manufacture / Packing / Import",
        description="The month and year in which the commodity is manufactured or pre-packed or imported shall be clearly indicated without ambiguity.",
        severity=RuleSeverity.CRITICAL,
        target_declaration=DeclarationType.DATE_OF_MANUFACTURE,
        penalty_section="Section 36(1), Legal Metrology Act, 2009"
    ),
    RuleDefinition(
        rule_id="LMR-R06-05",
        legal_reference="Rule 6(1)(e), Legal Metrology (Packaged Commodities) Rules, 2011",
        title="Maximum Retail Price (MRP) and Tax Inclusivity",
        description="The retail sale price shall be declared as 'Maximum Retail Price' or 'MRP' followed by currency symbol and must include the mandatory statement '(inclusive of all taxes)'.",
        severity=RuleSeverity.CRITICAL,
        target_declaration=DeclarationType.RETAIL_SALE_PRICE,
        penalty_section="Section 36(1), Legal Metrology Act, 2009"
    ),
    RuleDefinition(
        rule_id="LMR-R06-06",
        legal_reference="Rule 6(11), Legal Metrology (Packaged Commodities) Amendment Rules, 2022",
        title="Unit Sale Price (USP) Declaration",
        description="Where net quantity is greater than 100g or 100ml, unit sale price (e.g. ₹ / g, ₹ / ml, ₹ / 100g) must be declared and must mathematically equal MRP divided by net quantity.",
        severity=RuleSeverity.CRITICAL,
        target_declaration=DeclarationType.UNIT_SALE_PRICE,
        penalty_section="Rule 6(11), Legal Metrology (PC) Amendment Rules, 2022"
    ),
    RuleDefinition(
        rule_id="LMR-R06-07",
        legal_reference="Rule 6(1)(n), Legal Metrology (Packaged Commodities) Rules, 2011",
        title="Consumer Care Helpline & Grievance Contact",
        description="The package shall bear the name, address, telephone number, and email address of the person or office that can be contacted in case of consumer complaints.",
        severity=RuleSeverity.MAJOR,
        target_declaration=DeclarationType.CONSUMER_CARE,
        penalty_section="Section 36(1), Legal Metrology Act, 2009"
    ),
    RuleDefinition(
        rule_id="LMR-R06-08",
        legal_reference="Rule 6(10), Legal Metrology (Packaged Commodities) Rules, 2011",
        title="Country of Origin Declaration",
        description="Every package containing imported or domestic goods shall clearly mention the name of the country of origin or manufacture.",
        severity=RuleSeverity.CRITICAL,
        target_declaration=DeclarationType.COUNTRY_OF_ORIGIN,
        penalty_section="Section 36(1), Legal Metrology Act, 2009"
    ),
    RuleDefinition(
        rule_id="LMR-SCH-02",
        legal_reference="Schedule II, Legal Metrology (Packaged Commodities) Rules, 2011",
        title="Minimum Height of Numerals and Letters on PDP",
        description="The height of any numeral and letter in the net quantity and MRP declaration shall not be less than the minimum height specified in Schedule II based on the Principal Display Panel area.",
        severity=RuleSeverity.MAJOR,
        target_declaration=DeclarationType.NET_QUANTITY,
        penalty_section="Schedule II, Legal Metrology (PC) Rules, 2011"
    ),
]
