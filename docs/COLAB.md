# Official Investigation Station — Google Colab

The canonical machine is `notebooks/Tropeiro_Intel_Official_Colab.ipynb`.

## Guided UX in 4.1

The notebook adds a beginner-first interface without removing advanced controls.

### Dynamic target field

Supported guided types:

- AUTO;
- DOMAIN;
- URL;
- IP;
- EMAIL;
- HASH;
- PHONE;
- MULTI_IOC;
- LURE_TEXT.

The visible field label and placeholder change with the selected/detected type.

Internally, the assistant continues populating the stable `SEEDS`, `MANUAL_IOCS` and `LURE_TEXT` variables so backend compatibility is preserved.

### Automatic scan plan

The default plan derives recommended modules from:

- input type;
- mode;
- provider budget;
- available secrets;
- brand context;
- number of targets.

Advanced analysts can disable automatic planning and manually change feature checkboxes.

### Instruction card before every execution

Every executable cell is preceded by a help card explaining:

- objective;
- how to use;
- expected output;
- what to do if it fails;
- common errors;
- whether the investigation can continue.

The larger notebook is intentional: the investigation should be inspectable rather than hidden behind one opaque button.

## Modes

- `PASSIVE` — recommended default.
- `SAFE_ENRICHMENT` — broader passive enrichment.
- `AUTHORIZED_ACTIVE` — only for explicitly authorized assets; active probing remains opt-in.

## Beginner documentation

- [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md)
- [SEARCH_TYPES.md](SEARCH_TYPES.md)
- [COMMON_ERRORS.md](COMMON_ERRORS.md)
- [GLOSSARY.md](GLOSSARY.md)

## Compatibility

The guided layer orchestrates backend variables. Collection, correlation, attribution and reporting logic remain in the `tropeiro/` package.
