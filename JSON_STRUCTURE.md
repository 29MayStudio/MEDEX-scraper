# JSON Structure and Usage Guide

This repository crawls, structures, and automatically publishes high-quality pharmaceutical datasets of Bangladesh's medicines. Every release contains three key JSON datasets linked via relational IDs, enabling developers to build apps, run analysis, or integrate them into other databases.

---

## Datasets Overview

The following three JSON files are published in every release:
1. **`medicine_data.json`**: Brand-specific details (name, strength, packaging, dosage, etc.) and relationships to generics and manufacturers.
2. **`generic_data.json`**: Deep monograph information (indications, pharmacology, dosage, side effects, precautions, etc.) for each generic drug.
3. **`manufacturer_data.json`**: Information about pharmaceutical manufacturers.

---

## 1. JSON Schema & Fields

### `medicine_data.json`
Represents individual medicine brands/products.

```json
[
  {
    "id": 1,
    "brand_id": 13717,
    "brand_name": "3 Bion",
    "type": "allopathic",
    "slug": "3-bion-tablet-100-mg",
    "dosage_form": "Tablet",
    "generic": "Vitamin B1, B6 & B12",
    "generic_id": 1135,
    "strength": "100 mg+200 mg+200 mcg",
    "manufacturer": "Jenphar Bangladesh Ltd.",
    "manufacturer_id": 39,
    "package_container": "box",
    "pack_size_info": "30's pack: ৳ 300.00",
    "created": "2026-07-27 07:49:55",
    "updated": "2026-07-27 07:49:55"
  }
]
```

- **`brand_id`**: The external unique identifier for the medicine on Medex.
- **`brand_name`**: Name of the brand.
- **`type`**: `allopathic` or `herbal`.
- **`slug`**: URL-friendly version of the medicine name.
- **`dosage_form`**: E.g., `Tablet`, `Syrup`, `Ophthalmic Solution`.
- **`generic`**: Name of the active generic ingredient.
- **`generic_id`**: Corresponding identifier linking to `generic_data.json`.
- **`strength`**: Strength of the brand.
- **`manufacturer`**: Name of the manufacturer.
- **`manufacturer_id`**: Corresponding identifier linking to `manufacturer_data.json`.
- **`package_container`**: Description of package container.
- **`pack_size_info`**: Standard packaging pricing and count info.

---

### `generic_data.json`
Represents the generic ingredients with detailed clinical descriptions.

```json
[
  {
    "id": 1,
    "generic_id": 1135,
    "generic_name": "Vitamin B1, B6 & B12",
    "monograph_link": null,
    "drug_class": "Herbal and Nutraceuticals",
    "indication": "Neuropathy and deficiency syndromes",
    "indication_description": "<div class=\"ac-body\">\nThis combination is indicated where a deficiency of the relevant vitamins exists...",
    "therapeutic_class_description": "<div class=\"ac-body\">\nHerbal and Nutraceuticals...",
    "pharmacology_description": "<div class=\"ac-body\">\nVitamin B1 converts carbohydrates...",
    "dosage_description": "<div class=\"ac-body\">\n1-3 tablets daily...",
    "administration_description": null,
    "interaction_description": null,
    "contraindications_description": null,
    "side_effects_description": null,
    "pregnancy_and_lactation_description": null,
    "precautions_description": null,
    "pediatric_usage_description": null,
    "overdose_effects_description": null,
    "duration_of_treatment_description": null,
    "reconstitution_description": null,
    "storage_conditions_description": null,
    "descriptions_count": 4,
    "created": "2026-07-27 07:49:55",
    "updated": "2026-07-27 07:49:55"
  }
]
```

---

### `manufacturer_data.json`
Represents pharmaceutical companies.

```json
[
  {
    "id": 1,
    "manufacturer_id": 39,
    "manufacturer_name": "Jenphar Bangladesh Ltd.",
    "slug": "jenphar-bangladesh-ltd-39",
    "generics_count": null,
    "brand_names_count": null,
    "created": "2026-07-27 07:49:55",
    "updated": "2026-07-27 07:49:55"
  }
]
```

---

## 2. How to Use the Data Anywhere

Because the datasets include standard link keys (`generic_id` and `manufacturer_id`), they are highly relational and easy to query or load.

### Code Examples

#### A. Python
To resolve relationship data (e.g. mapping a medicine to its generic monograph or its manufacturer):

```python
import json

# Load files
with open("medicine_data.json", "r", encoding="utf-8") as f:
    medicines = json.load(f)

with open("generic_data.json", "r", encoding="utf-8") as f:
    generics = {g["generic_id"]: g for g in json.load(f)}

with open("manufacturer_data.json", "r", encoding="utf-8") as f:
    manufacturers = {m["manufacturer_id"]: m for m in json.load(f)}

# Query & join relationships
for med in medicines[:5]:
    name = med["brand_name"]
    gen_id = med["generic_id"]
    man_id = med["manufacturer_id"]

    generic_info = generics.get(gen_id, {})
    manufacturer_info = manufacturers.get(man_id, {})

    print(f"Brand: {name} ({med['strength']})")
    print(f"  Manufacturer: {manufacturer_info.get('manufacturer_name', 'Unknown')}")
    print(f"  Generic Monograph Link: {generic_info.get('monograph_link', 'None')}")
```

#### B. JavaScript / Node.js
```javascript
const fs = require('fs');

// Load files
const medicines = JSON.parse(fs.readFileSync('medicine_data.json', 'utf8'));
const genericsList = JSON.parse(fs.readFileSync('generic_data.json', 'utf8'));
const manufacturersList = JSON.parse(fs.readFileSync('manufacturer_data.json', 'utf8'));

// Build lookup maps
const genericsMap = new Map(genericsList.map(g => [g.generic_id, g]));
const manufacturersMap = new Map(manufacturersList.map(m => [m.manufacturer_id, m]));

// Map first 5 records with relationships
medicines.slice(0, 5).forEach(med => {
    const generic = genericsMap.get(med.generic_id) || {};
    const manufacturer = manufacturersMap.get(med.manufacturer_id) || {};

    console.log(`Medicine: ${med.brand_name} [${med.dosage_form}]`);
    console.log(`  Manufactured by: ${manufacturer.manufacturer_name || 'N/A'}`);
    console.log(`  Pharmacology: ${generic.pharmacology_description || 'No description available'}`);
});
```
