Html
    - code

    .from_path()
        - path

Style, JavaScript
    - code
    - priority

    .from_path()
        - path
        - priority

    .from_url()
        - url
        - priority


Element
    - name
    - position
    - width
    - showif

Row
    - *elements
    - height
    - valign_cols

    - name
    - showif


TextElement
    - text
    - align

    - name
    - position
    - width
    - showif

    .from_path
        - path
        - align

TextEntryElement
    - leftlab
    - rightlab
    - toplab

    - prefix
    - suffix
    
    - placeholder
    - default
    - force_input
    - description

    - name
    - position
    - width
    - showif

SingleChoiceElement
    - *choices
    
    - leftlab
    - rightlab
    - toplab

    - vertical
    - align

    - default
    - force_input
    - description

    - name
    - position
    - width
    - showif


